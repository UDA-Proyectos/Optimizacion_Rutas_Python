"""Prepara los datos del OSRM local (perfil `driving`, algoritmo MLD) para el Gran Mendoza.

Se corre una sola vez (o cuando se quiera refrescar el mapa):

    uv run python scripts/preparar_osrm.py

y después se levanta el servicio con `docker compose --profile osrm up -d osrm`.

Por defecto NO baja el extracto de toda Argentina (Geofabrik, cientos de MB, y
`osrm-extract` necesita varios GB de RAM): le pide a Overpass solo las calles del
recuadro del Gran Mendoza, por teselas chicas (una consulta grande da 504), las
fusiona y las procesa en pocos minutos con poca memoria. Con `--extracto` se puede
usar en cambio un `.osm.pbf` propio (ej. el de Argentina completo si la máquina
tiene RAM de sobra).
"""

import argparse
import math
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent.parent
DIRECTORIO_DATOS = RAIZ / "data" / "osrm"
# Misma versión que docker-compose.yml: los datos preparados solo los lee el
# osrm-routed de la misma versión mayor. Docker Hub quedó en la v5.25 (2021); las
# versiones nuevas se publican en el registro de GitHub del proyecto.
IMAGEN_OSRM = "ghcr.io/project-osrm/osrm-backend:v5.27.1"
NOMBRE_BASE = "mendoza"
# Se prueban en orden: son instancias públicas y a veces una está saturada.
SERVIDORES_OVERPASS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
USER_AGENT = "optimizacion-rutas-gran-mendoza/1.0 (proyecto academico CACIC 2026; preparar_osrm.py)"

# min_lon, min_lat, max_lon, max_lat — Capital, Godoy Cruz, Guaymallén, Las Heras,
# Luján de Cuyo y Maipú, con margen.
BBOX_GRAN_MENDOZA = "-69.02,-33.06,-68.66,-32.76"
# Lado (en grados, ~9 km) de cada tesela: más grande que esto, Overpass da 504.
LADO_TESELA = 0.08
# Una tesela que Overpass no resuelve se divide en 4, hasta este lado (~2 km).
LADO_MINIMO_TESELA = 0.02
REINTENTOS_TESELA_MINIMA = 5

# El perfil `driving` ignora estos tipos de camino: no vale la pena bajarlos.
CAMINOS_NO_TRANSITABLES = (
    "footway|path|steps|pedestrian|cycleway|bridleway|corridor|elevator|"
    "proposed|construction|platform|raceway"
)


def consulta_overpass(min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> str:
    # Overpass espera (sur, oeste, norte, este).
    recuadro = f"{min_lat},{min_lon},{max_lat},{max_lon}"
    return (
        "[out:xml][timeout:100];"
        f'way["highway"]["highway"!~"^({CAMINOS_NO_TRANSITABLES})$"]({recuadro});'
        "(._;>;);"
        "out;"
    )


def teselas(bbox: str, lado: float) -> list[tuple[float, float, float, float]]:
    min_lon, min_lat, max_lon, max_lat = (float(valor) for valor in bbox.split(","))
    columnas = max(1, math.ceil((max_lon - min_lon) / lado))
    filas = max(1, math.ceil((max_lat - min_lat) / lado))
    ancho, alto = (max_lon - min_lon) / columnas, (max_lat - min_lat) / filas
    return [
        (
            min_lon + columna * ancho,
            min_lat + fila * alto,
            min_lon + (columna + 1) * ancho,
            min_lat + (fila + 1) * alto,
        )
        for fila in range(filas)
        for columna in range(columnas)
    ]


Tesela = tuple[float, float, float, float]


def pedir_tesela(tesela: Tesela, destino: Path, errores: list[str]) -> bool:
    """Un intento por servidor. Devuelve False si ninguno pudo (y deja los motivos
    en `errores`), para que el caller decida si dividir la tesela."""
    consulta = consulta_overpass(*tesela)
    for servidor in SERVIDORES_OVERPASS:
        try:
            with requests.post(
                servidor,
                data={"data": consulta},
                # Overpass rechaza (406) los pedidos sin un User-Agent identificable.
                headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
                timeout=(15, 130),
            ) as respuesta:
                respuesta.raise_for_status()
                destino.write_bytes(respuesta.content)
                return True
        except requests.exceptions.RequestException as error:
            errores.append(f"{servidor}: {error}")
    return False


def dividir(tesela: Tesela) -> list[Tesela]:
    min_lon, min_lat, max_lon, max_lat = tesela
    medio_lon, medio_lat = (min_lon + max_lon) / 2, (min_lat + max_lat) / 2
    return [
        (min_lon, min_lat, medio_lon, medio_lat),
        (medio_lon, min_lat, max_lon, medio_lat),
        (min_lon, medio_lat, medio_lon, max_lat),
        (medio_lon, medio_lat, max_lon, max_lat),
    ]


def bajar_tesela(tesela: Tesela, nombre: str, directorio: Path) -> list[Path]:
    """Archivos que cubren la tesela: uno si Overpass la resuelve a tiempo, o los de
    sus cuatro cuartos (recursivamente) si es demasiado densa — el centro de la
    ciudad da 504 con el tamaño de tesela que anda bien en las afueras."""
    archivo = directorio / f"{nombre}.osm"
    # Una tesela ya bajada se reutiliza: si el script se corta, no se empieza de cero.
    if archivo.exists():
        return [archivo]

    errores: list[str] = []
    if pedir_tesela(tesela, archivo, errores):
        time.sleep(1)  # cortesía con un servicio público
        return [archivo]

    if max(tesela[2] - tesela[0], tesela[3] - tesela[1]) <= LADO_MINIMO_TESELA:
        # Ya no se puede dividir más: el fallo es del servicio (saturado o caído un
        # rato), no del tamaño. Se reintenta con esperas crecientes antes de rendirse.
        for intento in range(1, REINTENTOS_TESELA_MINIMA + 1):
            print(
                f"  {nombre}: reintento {intento}/{REINTENTOS_TESELA_MINIMA} en {15 * intento}s..."
            )
            time.sleep(15 * intento)
            if pedir_tesela(tesela, archivo, errores):
                return [archivo]
        raise SystemExit(
            f"No se pudo bajar la tesela {tesela} ni dividiéndola:\n  "
            + "\n  ".join(errores[-len(SERVIDORES_OVERPASS) :])
            + "\nProbá de nuevo en unos minutos, o pasá un extracto propio con --extracto."
        )
    print(f"  {nombre} es demasiado densa para Overpass: la divido en 4.")
    return [
        archivo_cuarto
        for indice, cuarto in enumerate(dividir(tesela))
        for archivo_cuarto in bajar_tesela(cuarto, f"{nombre}_{indice}", directorio)
    ]


def fusionar(archivos: list[Path], destino: Path) -> None:
    """Junta las teselas en un solo .osm sin repetir elementos: un camino que cruza
    el borde entre dos teselas viene completo en ambas. OSM XML exige nodos antes
    que caminos."""
    nodos: dict[int, str] = {}
    caminos: dict[int, str] = {}
    for archivo in archivos:
        for _, elemento in ET.iterparse(archivo, events=("end",)):
            if elemento.tag == "node":
                nodos[int(elemento.attrib["id"])] = ET.tostring(elemento, encoding="unicode")
            elif elemento.tag == "way":
                caminos[int(elemento.attrib["id"])] = ET.tostring(elemento, encoding="unicode")
            else:
                continue
            elemento.clear()

    parcial = destino.with_suffix(destino.suffix + ".parcial")
    with parcial.open("w", encoding="utf-8") as salida:
        salida.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n<osm version="0.6" generator="preparar_osrm">\n'
        )
        for id_nodo in sorted(nodos):
            salida.write(nodos[id_nodo].strip() + "\n")
        for id_camino in sorted(caminos):
            salida.write(caminos[id_camino].strip() + "\n")
        salida.write("</osm>\n")
    parcial.replace(destino)
    print(f"  {len(nodos)} nodos y {len(caminos)} caminos únicos.")


def descargar_calles(bbox: str, destino: Path) -> None:
    lista = teselas(bbox, LADO_TESELA)
    print(f"Bajando las calles del recuadro {bbox} en {len(lista)} teselas (Overpass)...")
    directorio_teselas = DIRECTORIO_DATOS / "teselas"
    directorio_teselas.mkdir(exist_ok=True)
    archivos = []
    for indice, tesela in enumerate(lista, start=1):
        bajados = bajar_tesela(tesela, f"tesela_{indice:03d}", directorio_teselas)
        peso = sum(archivo.stat().st_size for archivo in bajados) / 1_000_000
        print(f"  tesela {indice}/{len(lista)} lista ({peso:.1f} MB)")
        archivos += bajados
    print("Fusionando teselas...")
    fusionar(archivos, destino)
    shutil.rmtree(directorio_teselas)
    print(f"Listo: {destino.name} ({destino.stat().st_size / 1_000_000:.1f} MB)")


def correr_osrm(*argumentos: str) -> None:
    subprocess.run(
        ["docker", "run", "--rm", "-v", f"{DIRECTORIO_DATOS}:/data", IMAGEN_OSRM, *argumentos],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--bbox",
        default=BBOX_GRAN_MENDOZA,
        help="min_lon,min_lat,max_lon,max_lat de las calles a bajar (default: Gran Mendoza)",
    )
    parser.add_argument(
        "--extracto",
        type=Path,
        help="usar este .osm.pbf en vez de bajar las calles de Overpass",
    )
    parser.add_argument("--forzar", action="store_true", help="volver a bajar aunque ya exista")
    args = parser.parse_args()

    DIRECTORIO_DATOS.mkdir(parents=True, exist_ok=True)

    if args.extracto:
        entrada = DIRECTORIO_DATOS / f"{NOMBRE_BASE}.osm.pbf"
        shutil.copyfile(args.extracto, entrada)
    else:
        entrada = DIRECTORIO_DATOS / f"{NOMBRE_BASE}.osm"
        if args.forzar or not entrada.exists():
            descargar_calles(args.bbox, entrada)
        else:
            print(f"Reutilizo {entrada.name} (usá --forzar para volver a bajarlo).")

    base = f"/data/{NOMBRE_BASE}.osrm"
    print("osrm-extract...")
    correr_osrm("osrm-extract", "-p", "/opt/car.lua", f"/data/{entrada.name}")
    print("osrm-partition...")
    correr_osrm("osrm-partition", base)
    print("osrm-customize...")
    correr_osrm("osrm-customize", base)

    print(
        "\nDatos de OSRM listos. Levantalo con:\n"
        "  docker compose --profile osrm up -d osrm\n"
        "y apuntá OSRM_BASE_URL a http://localhost:5001 en tu .env."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
