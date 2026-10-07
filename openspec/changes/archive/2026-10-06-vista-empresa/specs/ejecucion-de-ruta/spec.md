## ADDED Requirements

### Requirement: Ejecución por el chofer de empresa
El sistema SHALL permitir al chofer de empresa ejecutar su ruta en curso con las mismas acciones y reglas que el chofer independiente: registrar llegada, completar, informar que no pudo entregar con motivo, saltear y cerrar la ruta. Al informar que no pudo entregar, MUST NOT ofrecerle reprogramar la entrega: la incidencia queda pendiente para que decida el admin.

#### Scenario: Completar paradas
- **WHEN** el chofer de empresa completa la parada en curso de su ruta asignada
- **THEN** la parada queda completada y pasa la siguiente, igual que para el chofer independiente

#### Scenario: No pude entregar
- **WHEN** el chofer de empresa informa que no pudo entregar, con un motivo
- **THEN** la parada queda fallida, se crea una incidencia pendiente y no se reprograma nada

#### Scenario: Pedido de reprogramar desde el chofer de empresa
- **WHEN** un chofer de empresa envía el pedido de fallar una parada con reprogramar activado
- **THEN** el sistema responde 403 y la parada no cambia
