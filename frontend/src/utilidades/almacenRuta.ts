import type { UsuarioPublico } from "../tipos/auth";
import type { RutaPublica } from "../tipos/ruta";

/** Copia local para poder abrir la app y ver la ruta sin conexión: la última
 * ruta activa consultada y el perfil del usuario (para no mandarlo al login
 * cuando `/me` falla solo por falta de red). Va en IndexedDB y no en
 * localStorage (que el CLAUDE.md descarta para la sesión). Guarda datos
 * operativos y de perfil, nunca credenciales ni el token, que sigue en la
 * cookie httpOnly. Todo best-effort: si IndexedDB no está disponible, la app
 * funciona igual pero sin modo offline. */
const NOMBRE_DB = "optiruta";
const VERSION_DB = 2;
const ALMACEN = "offline";
const CLAVE_RUTA = "ruta";
const CLAVE_RUTAS = "rutas";
const CLAVE_USUARIO = "usuario";

export interface RutaGuardada {
  ruta: RutaPublica;
  guardadaEn: number;
}

function abrirDb(): Promise<IDBDatabase> {
  return new Promise((resolver, rechazar) => {
    const pedido = indexedDB.open(NOMBRE_DB, VERSION_DB);
    pedido.onupgradeneeded = () => {
      const db = pedido.result;
      // v1 guardaba solo la ruta en un almacén "ruta"; v2 unifica todo en "offline".
      if (db.objectStoreNames.contains("ruta")) {
        db.deleteObjectStore("ruta");
      }
      if (!db.objectStoreNames.contains(ALMACEN)) {
        db.createObjectStore(ALMACEN);
      }
    };
    pedido.onsuccess = () => resolver(pedido.result);
    pedido.onerror = () => rechazar(pedido.error);
  });
}

async function operar<T>(
  modo: IDBTransactionMode,
  accion: (almacen: IDBObjectStore) => IDBRequest<T> | void,
): Promise<T | undefined> {
  try {
    const db = await abrirDb();
    return await new Promise<T | undefined>((resolver) => {
      const transaccion = db.transaction(ALMACEN, modo);
      const pedido = accion(transaccion.objectStore(ALMACEN));
      transaccion.oncomplete = () => {
        db.close();
        resolver(pedido ? pedido.result : undefined);
      };
      transaccion.onerror = transaccion.onabort = () => {
        db.close();
        resolver(undefined);
      };
    });
  } catch {
    return undefined;
  }
}

export async function guardarRutaCache(ruta: RutaPublica): Promise<void> {
  const valor: RutaGuardada = { ruta, guardadaEn: Date.now() };
  await operar("readwrite", (almacen) => almacen.put(valor, CLAVE_RUTA));
}

export async function leerRutaCache(): Promise<RutaGuardada | null> {
  return (await operar<RutaGuardada>("readonly", (almacen) => almacen.get(CLAVE_RUTA))) ?? null;
}

export async function borrarRutaCache(): Promise<void> {
  await operar("readwrite", (almacen) => almacen.delete(CLAVE_RUTA));
}

export async function guardarUsuarioCache(usuario: UsuarioPublico): Promise<void> {
  await operar("readwrite", (almacen) => almacen.put(usuario, CLAVE_USUARIO));
}

export async function leerUsuarioCache(): Promise<UsuarioPublico | null> {
  return (await operar<UsuarioPublico>("readonly", (almacen) => almacen.get(CLAVE_USUARIO))) ?? null;
}

/** Las rutas de un día, más la ruta en curso (que puede ser de otro día), tal
 * como se vieron la última vez con conexión. */
export interface RutasGuardadas {
  fecha: string;
  rutas: RutaPublica[];
  enCurso: RutaPublica | null;
  guardadaEn: number;
}

export async function guardarRutasCache(
  datos: Omit<RutasGuardadas, "guardadaEn">,
): Promise<void> {
  const valor: RutasGuardadas = { ...datos, guardadaEn: Date.now() };
  await operar("readwrite", (almacen) => almacen.put(valor, CLAVE_RUTAS));
}

export async function leerRutasCache(): Promise<RutasGuardadas | null> {
  return (await operar<RutasGuardadas>("readonly", (almacen) => almacen.get(CLAVE_RUTAS))) ?? null;
}

/** Todo lo guardado para uso offline — al cerrar sesión o ante un 401. */
export async function borrarCacheOffline(): Promise<void> {
  await operar("readwrite", (almacen) => {
    almacen.delete(CLAVE_RUTA);
    almacen.delete(CLAVE_RUTAS);
    almacen.delete(CLAVE_USUARIO);
  });
}
