## ADDED Requirements

### Requirement: Incidencias del chofer de empresa
El sistema SHALL permitir al chofer de empresa reportar una incidencia sobre su ruta en curso y consultar las que reportó, con los mismos tipos, estados y filtros que el chofer independiente.

#### Scenario: Reportar durante la ruta
- **WHEN** el chofer de empresa reporta una incidencia con una ruta en curso
- **THEN** la incidencia queda pendiente, asociada a su ruta, y la ve el admin de su empresa

#### Scenario: Consultar las propias
- **WHEN** el chofer de empresa consulta sus incidencias
- **THEN** ve solo las de sus rutas, sin acciones para resolverlas

## MODIFIED Requirements

### Requirement: Resolver una incidencia
El sistema SHALL permitir resolver una incidencia pendiente eligiendo entre reprogramar la entrega (solo si la incidencia proviene de una parada fallida) o cerrarla sin más acción, y SHALL registrar la resolución. El chofer independiente resuelve las suyas; en una empresa, las resuelve el admin, sobre cualquier incidencia de su flota, y el chofer de empresa MUST NOT resolverlas.

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

#### Scenario: Admin resuelve una incidencia de su flota
- **WHEN** el admin resuelve como reprogramada una incidencia pendiente de una parada fallida de un chofer de su empresa
- **THEN** la incidencia queda resuelta y la entrega queda pendiente para la empresa

#### Scenario: Chofer de empresa intenta resolver
- **WHEN** un chofer de empresa intenta resolver una incidencia
- **THEN** el sistema responde 403 y la incidencia sigue pendiente

#### Scenario: Incidencia de otra empresa
- **WHEN** el admin intenta resolver una incidencia de otra empresa
- **THEN** el sistema responde 404
