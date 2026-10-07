## ADDED Requirements

### Requirement: Lugares y depósitos de una empresa
En una empresa, los lugares y depósitos SHALL ser compartidos por toda la flota, y solo el admin SHALL poder crearlos, editarlos o darlos de baja. El chofer independiente mantiene su propia libreta sin cambios.

#### Scenario: Admin gestiona la libreta
- **WHEN** el admin crea, edita o da de baja un lugar o un depósito
- **THEN** el cambio queda en la libreta de la empresa y se ve al armar rutas para cualquier chofer de esa empresa

#### Scenario: Chofer de empresa intenta escribir
- **WHEN** un chofer de empresa intenta crear, editar o dar de baja un lugar o un depósito
- **THEN** el sistema responde 403 y la libreta no cambia
