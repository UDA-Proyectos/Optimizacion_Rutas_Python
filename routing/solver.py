from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from core.config import settings


def _es_cuadrada(matriz: list, lado: int) -> bool:
    return len(matriz) == lado and all(len(fila) == lado for fila in matriz)


def _validar_entradas(
    matriz_distancias: list,
    demandas: list,
    capacidades_vehiculos: list,
    matriz_tiempos: list | None,
    tiempos_servicio: list | None,
    ventanas_horarias: list | None,
    tipo_problema: str,
) -> None:
    """Falla con ValueError ante entradas inconsistentes entre sí, en vez de
    dejar que OR-Tools (o un IndexError en un callback) reviente sin un mensaje
    útil."""
    num_nodos = len(matriz_distancias)
    if num_nodos == 0 or not _es_cuadrada(matriz_distancias, num_nodos):
        raise ValueError("La matriz de distancias debe ser cuadrada y no estar vacía.")
    if len(demandas) != num_nodos:
        raise ValueError(
            f"La matriz de distancias tiene {num_nodos} nodos pero hay {len(demandas)} demandas."
        )
    if not capacidades_vehiculos:
        raise ValueError("Hace falta al menos un vehículo.")

    if tipo_problema == "VRPTW":
        if matriz_tiempos is None or not _es_cuadrada(matriz_tiempos, num_nodos):
            raise ValueError("La matriz de tiempos debe ser cuadrada y del mismo tamaño.")
        if tiempos_servicio is None or len(tiempos_servicio) != num_nodos:
            raise ValueError("Hace falta un tiempo de servicio por nodo.")
        if ventanas_horarias is None or len(ventanas_horarias) != num_nodos:
            raise ValueError("Hace falta una ventana horaria por nodo.")


def resolver_ruteo(
    matriz_distancias: list,
    demandas: list,
    capacidades_vehiculos: list,
    matriz_tiempos: list = None,
    tiempos_servicio: list = None,
    ventanas_horarias: list = None,
    tipo_problema: str = "CVRP",
) -> dict:

    num_nodos = len(matriz_distancias)
    num_vehiculos = len(capacidades_vehiculos)
    nodo_deposito = 0

    _validar_entradas(
        matriz_distancias,
        demandas,
        capacidades_vehiculos,
        matriz_tiempos,
        tiempos_servicio,
        ventanas_horarias,
        tipo_problema,
    )

    manager = pywrapcp.RoutingIndexManager(num_nodos, num_vehiculos, nodo_deposito)
    routing = pywrapcp.RoutingModel(manager)

    # 1. Función de Costo (Distancias reales de OSRM)
    def callback_distancia(from_index, to_index):
        origen = manager.IndexToNode(from_index)
        destino = manager.IndexToNode(to_index)
        return int(matriz_distancias[origen][destino])

    indice_transito = routing.RegisterTransitCallback(callback_distancia)
    routing.SetArcCostEvaluatorOfAllVehicles(indice_transito)

    # 2. Dimensión de Capacidad (CVRP)
    def callback_demanda(from_index):
        origen = manager.IndexToNode(from_index)
        return demandas[origen]

    indice_demanda = routing.RegisterUnaryTransitCallback(callback_demanda)
    routing.AddDimensionWithVehicleCapacity(
        indice_demanda,
        0,  # Sin holgura
        capacidades_vehiculos,
        True,
        "Capacidad",
    )

    # 3. Dimensión de Tiempo (VRPTW)
    if tipo_problema == "VRPTW":

        def callback_tiempo(from_index, to_index):
            origen = manager.IndexToNode(from_index)
            destino = manager.IndexToNode(to_index)
            # OSRM devuelve segundos, lo pasamos a minutos y sumamos el servicio de descarga
            tiempo_viaje_minutos = int(matriz_tiempos[origen][destino] / 60)
            tiempo_descarga = tiempos_servicio[origen]
            return tiempo_viaje_minutos + tiempo_descarga

        indice_tiempo = routing.RegisterTransitCallback(callback_tiempo)

        # Agregamos la restricción de tiempo
        routing.AddDimension(
            indice_tiempo,
            120,  # Holgura (Tiempo máximo de espera si el camión llega antes que abra el cliente)
            1440,  # Tiempo máximo total por vehículo (ej. 24 hs = 1440 mins)
            False,
            "Tiempo",
        )
        dimension_tiempo = routing.GetDimensionOrDie("Tiempo")

        # Aplicamos las ventanas horarias a cada nodo
        for i in range(num_nodos):
            # Obtenemos inicio y fin (ej: abre al minuto 480 [8AM], cierra al minuto 600 [10AM])
            inicio, fin = ventanas_horarias[i]
            index = manager.NodeToIndex(i)
            dimension_tiempo.CumulVar(index).SetRange(inicio, fin)

        # Aplicamos la ventana del depósito a los vehículos al salir y volver
        inicio_deposito, fin_deposito = ventanas_horarias[0]
        for i in range(num_vehiculos):
            dimension_tiempo.CumulVar(routing.Start(i)).SetRange(inicio_deposito, fin_deposito)
            dimension_tiempo.CumulVar(routing.End(i)).SetRange(inicio_deposito, fin_deposito)

    # 4. Estrategia de Búsqueda
    parametros_busqueda = pywrapcp.DefaultRoutingSearchParameters()
    parametros_busqueda.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    parametros_busqueda.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    parametros_busqueda.time_limit.seconds = settings.solver_time_limit_segundos

    # 5. Resolver
    solucion = routing.SolveWithParameters(parametros_busqueda)

    # 6. Serialización de Salida
    if not solucion:
        return {"estado": "Fallo", "mensaje": "No se encontró solución factible."}

    rutas_vehiculos = []
    distancia_total = 0

    for id_vehiculo in range(num_vehiculos):
        indice = routing.Start(id_vehiculo)
        ruta = []
        carga_ruta = 0
        distancia_ruta = 0

        while not routing.IsEnd(indice):
            nodo_actual = manager.IndexToNode(indice)
            carga_ruta += demandas[nodo_actual]

            # Recolectamos la información del nodo
            info_nodo = {"nodo_id": nodo_actual}

            # Si es VRPTW, extraemos el minuto exacto de llegada calculado por el modelo
            if tipo_problema == "VRPTW":
                dimension_tiempo = routing.GetDimensionOrDie("Tiempo")
                var_tiempo = dimension_tiempo.CumulVar(indice)
                info_nodo["minuto_llegada"] = solucion.Min(var_tiempo)

            ruta.append(info_nodo)

            indice_anterior = indice
            indice = solucion.Value(routing.NextVar(indice))
            distancia_ruta += routing.GetArcCostForVehicle(indice_anterior, indice, id_vehiculo)

        # Agregamos la última parada (vuelta al depósito)
        info_nodo_final = {"nodo_id": manager.IndexToNode(indice)}
        if tipo_problema == "VRPTW":
            var_tiempo = dimension_tiempo.CumulVar(indice)
            info_nodo_final["minuto_llegada"] = solucion.Min(var_tiempo)

        ruta.append(info_nodo_final)

        rutas_vehiculos.append(
            {
                "vehiculo": id_vehiculo,
                "ruta_secuencial_nodos": ruta,
                "carga_total": carga_ruta,
                "distancia_recorrida_metros": distancia_ruta,
            }
        )
        distancia_total += distancia_ruta

    return {"estado": "Exito", "rutas": rutas_vehiculos, "distancia_total_flota": distancia_total}
