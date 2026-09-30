## MODIFIED Requirements

### Requirement: Editar vehículo propio
El sistema SHALL permitir al chofer independiente modificar el tipo, la patente y la capacidad de carga de su vehículo, y SHALL garantizar que la patente siga siendo única.

#### Scenario: Cambio de capacidad sin ruta activa
- **WHEN** el chofer sin ninguna ruta planificada ni en curso cambia la capacidad a 300 kg
- **THEN** el vehículo se actualiza y las próximas planificaciones usan 300 kg

#### Scenario: Patente duplicada
- **WHEN** el chofer usa la patente de otro vehículo
- **THEN** el sistema responde 409 y no modifica el vehículo

#### Scenario: Ruta activa
- **WHEN** el chofer intenta cambiar la capacidad o la patente con una ruta planificada o en curso
- **THEN** el sistema responde 409 indicando que debe terminar o cancelar la ruta

#### Scenario: Ruta planificada para otro día
- **WHEN** el chofer intenta cambiar la capacidad con una ruta planificada para un día futuro
- **THEN** el sistema responde 409, porque esa ruta se planificó con la capacidad actual

#### Scenario: Capacidad inválida
- **WHEN** el chofer envía una capacidad menor o igual a 0
- **THEN** el sistema responde 422
