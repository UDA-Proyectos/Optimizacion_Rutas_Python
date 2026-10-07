# resumen-y-historial-de-ruta Specification

## Purpose
Muestra a cada chofer (independiente o de empresa) cómo resultó realmente una ruta terminada, tanto al cerrarla como al consultarla después en el historial.

## Requirements

### Requirement: Resumen de una ruta terminada
El sistema SHALL calcular para toda ruta completada un resumen con: duración real (de inicio a fin), cantidad de paradas completadas, fallidas y salteadas, carga entregada en kg, cantidad de incidencias y, si la ruta usó ventanas horarias, cantidad y porcentaje de ventanas cumplidas.

#### Scenario: Ruta con una parada fallida
- **WHEN** el chofer cierra una ruta de 5 paradas con 4 completadas y 1 fallida
- **THEN** el resumen indica 4 completadas, 1 fallida y suma solo la carga de las 4 entregadas

#### Scenario: Ruta sin ventanas horarias
- **WHEN** la ruta se planificó sin ventanas horarias
- **THEN** el resumen no incluye métricas de ventanas cumplidas

#### Scenario: Ruta no terminada
- **WHEN** se consulta el resumen de una ruta que no está completada
- **THEN** el sistema no devuelve duración real ni porcentaje de ventanas

### Requirement: Distancia informada como planificada
El sistema SHALL presentar la distancia como planificada y SHALL NOT presentarla como recorrida real mientras no exista un registro de la posición del vehículo.

#### Scenario: Etiqueta de distancia
- **WHEN** el chofer ve el resumen de una ruta terminada
- **THEN** la distancia aparece rotulada como planificada

### Requirement: Pantalla de cierre
El sistema SHALL mostrar el resumen al completarse la ruta, con acciones para volver a armar una ruta o ir al historial.

#### Scenario: Última parada entregada
- **WHEN** el chofer entrega la última parada pendiente
- **THEN** la pantalla de "Ruta de hoy" muestra el resumen de cierre en lugar de la vista en curso

### Requirement: Detalle real en el historial
El sistema SHALL mostrar en el detalle de un día del historial el resumen de esa ruta y el estado de cada parada, con el motivo cuando fue fallida.

#### Scenario: Día con parada fallida
- **WHEN** el chofer abre en el historial un día con una parada fallida por "cliente ausente"
- **THEN** ve esa parada marcada como fallida con el motivo

#### Scenario: Ruta cancelada
- **WHEN** el chofer abre un día cuya ruta fue cancelada
- **THEN** ve el estado "Cancelada" sin métricas de ejecución

### Requirement: Resultado en el calendario
El sistema SHALL indicar en el calendario mensual el resultado de cada día (completadas sobre total) y SHALL distinguir los días con al menos una parada fallida.

#### Scenario: Día con fallos
- **WHEN** el chofer ve un mes con una ruta que tuvo una parada fallida
- **THEN** ese día aparece marcado de forma distinta a un día sin fallos

### Requirement: Resumen e historial del chofer de empresa
El sistema SHALL mostrar al chofer de empresa la pantalla de cierre al terminar una ruta asignada, y SHALL permitirle consultar el historial y el detalle de sus propias rutas con el mismo resumen que el chofer independiente. MUST NOT mostrarle rutas de otros choferes de su empresa.

#### Scenario: Cierre de una ruta asignada
- **WHEN** el chofer de empresa termina su ruta
- **THEN** ve el resumen de cierre con duración, paradas completadas, fallidas y salteadas, y carga entregada

#### Scenario: Historial propio
- **WHEN** el chofer de empresa consulta su historial
- **THEN** ve solo sus rutas, no las de otros choferes de la empresa
