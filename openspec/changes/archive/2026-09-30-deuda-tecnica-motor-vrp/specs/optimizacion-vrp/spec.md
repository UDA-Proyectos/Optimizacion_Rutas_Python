## Purpose

Define el contrato de respuesta del endpoint de optimización pura del motor VRP, para que quien lo consuma distinga entre un pedido inválido, un problema sin solución y un fallo interno.

## ADDED Requirements

### Requirement: Problema sin solución responde 400
El sistema SHALL responder HTTP 400 con el mensaje del solver cuando el problema enviado a `/api/v1/optimizar` no tiene solución factible, y SHALL NOT responder 500 en ese caso.

#### Scenario: Demanda mayor a la capacidad
- **WHEN** se envía un problema cuya demanda total supera la capacidad de todos los vehículos
- **THEN** el sistema responde 400 con un mensaje que explica que no hay solución factible

#### Scenario: Ventanas horarias imposibles
- **WHEN** se envía un problema VRPTW con ventanas horarias que no pueden cumplirse
- **THEN** el sistema responde 400 con el mensaje del solver

### Requirement: Solución exitosa
El sistema SHALL responder 200 con las rutas de cada vehículo, su secuencia de nodos, la distancia y la carga, cuando existe una solución.

#### Scenario: Problema CVRP resoluble
- **WHEN** se envía un problema CVRP factible con matriz de distancias válida
- **THEN** el sistema responde 200 y todas las rutas comienzan y terminan en el depósito (nodo 0)

### Requirement: Fallos internos responden 500
El sistema SHALL responder HTTP 500 únicamente ante errores inesperados, y SHALL NOT convertir en 500 los errores de validación o de falta de solución.

#### Scenario: Error inesperado
- **WHEN** ocurre una excepción no prevista durante la resolución
- **THEN** el sistema responde 500 sin exponer detalles internos de la traza

### Requirement: Validación de entrada
El sistema SHALL responder 422 o 400 cuando las dimensiones de las matrices, las demandas o las ventanas horarias son inconsistentes entre sí.

#### Scenario: Matriz de tamaño incorrecto
- **WHEN** la matriz de distancias no es cuadrada o no coincide con la cantidad de nodos
- **THEN** el sistema rechaza el pedido con un error de validación
