## ADDED Requirements

### Requirement: Estado de una incidencia
El sistema SHALL mantener para cada incidencia un estado, pendiente o resuelta, y, cuando está resuelta, su resolución (reprogramada o cerrada) y la fecha. Las incidencias generadas por una entrega fallida SHALL nacer pendientes; las incidencias generales de la ruta también, hasta que el chofer las cierre.

#### Scenario: Incidencia nueva
- **WHEN** se crea una incidencia
- **THEN** su estado es pendiente y no tiene resolución

### Requirement: Filtrar incidencias por estado
El sistema SHALL permitir listar las incidencias del chofer filtrando por estado pendiente o resuelta, y SHALL devolver todas cuando no se indica filtro.

#### Scenario: Solo pendientes
- **WHEN** el chofer pide las incidencias pendientes
- **THEN** recibe únicamente las que no fueron resueltas

#### Scenario: Estado inválido
- **WHEN** el chofer filtra por un estado que no existe
- **THEN** el sistema responde 422

### Requirement: Resolver una incidencia
El sistema SHALL permitir al chofer resolver una incidencia pendiente propia, eligiendo entre reprogramar la entrega (solo si la incidencia proviene de una parada fallida) o cerrarla sin más acción, y SHALL registrar la resolución.

#### Scenario: Reprogramar desde una incidencia
- **WHEN** el chofer resuelve como reprogramada una incidencia pendiente de una parada fallida
- **THEN** la incidencia queda resuelta como reprogramada y la entrega queda pendiente para la próxima ruta

#### Scenario: Cerrar sin acción
- **WHEN** el chofer cierra una incidencia pendiente
- **THEN** queda resuelta como cerrada y no se crea ninguna entrega pendiente

#### Scenario: Reprogramar una incidencia sin parada fallida
- **WHEN** el chofer pide reprogramar una incidencia general o de una parada que no está fallida
- **THEN** el sistema responde 409 y la incidencia sigue pendiente

#### Scenario: Incidencia ya resuelta
- **WHEN** el chofer intenta resolver una incidencia que ya está resuelta
- **THEN** el sistema responde 409

#### Scenario: Incidencia ajena
- **WHEN** el chofer intenta resolver una incidencia de otro chofer
- **THEN** el sistema responde 404
