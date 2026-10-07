## ADDED Requirements

### Requirement: Resumen e historial del chofer de empresa
El sistema SHALL mostrar al chofer de empresa la pantalla de cierre al terminar una ruta asignada, y SHALL permitirle consultar el historial y el detalle de sus propias rutas con el mismo resumen que el chofer independiente. MUST NOT mostrarle rutas de otros choferes de su empresa.

#### Scenario: Cierre de una ruta asignada
- **WHEN** el chofer de empresa termina su ruta
- **THEN** ve el resumen de cierre con duración, paradas completadas, fallidas y salteadas, y carga entregada

#### Scenario: Historial propio
- **WHEN** el chofer de empresa consulta su historial
- **THEN** ve solo sus rutas, no las de otros choferes de la empresa
