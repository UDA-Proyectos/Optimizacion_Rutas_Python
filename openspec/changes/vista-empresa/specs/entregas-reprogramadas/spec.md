## MODIFIED Requirements

### Requirement: Listar entregas pendientes
El sistema SHALL listar las entregas reprogramadas todavía sin cumplir de su dueño, y SHALL omitir las de lugares dados de baja y las de otros dueños. El dueño es el chofer independiente o, en una empresa, la empresa: el admin ve todas las de su empresa, sin importar qué chofer falló la entrega.

#### Scenario: Listado propio
- **WHEN** el chofer independiente consulta sus entregas pendientes
- **THEN** recibe solo las suyas, con lugar, dirección, carga, bultos, ventana y fecha de origen

#### Scenario: Lugar dado de baja
- **WHEN** el lugar de una entrega reprogramada fue dado de baja de la libreta
- **THEN** esa entrega no aparece en el listado

#### Scenario: Entregas de la empresa
- **WHEN** el admin consulta las entregas pendientes
- **THEN** recibe las reprogramadas de toda su empresa, incluidas las que fallaron distintos choferes

#### Scenario: Chofer de empresa
- **WHEN** un chofer de empresa consulta las entregas pendientes
- **THEN** el sistema responde 403

### Requirement: Precarga al armar la ruta
El sistema SHALL precargar las entregas pendientes del dueño, ya seleccionadas y con sus datos, al armar una ruta nueva, y SHALL permitir desmarcarlas o modificar sus valores para esa ruta. En una empresa, las precarga al admin al armar una ruta para cualquiera de sus choferes.

#### Scenario: Ruta nueva con reprogramadas
- **WHEN** el chofer empieza a armar una ruta y tiene entregas pendientes
- **THEN** esos lugares aparecen marcados con su carga y se identifican como reprogramados

#### Scenario: Desmarcar
- **WHEN** el chofer desmarca una entrega reprogramada y confirma la ruta
- **THEN** la entrega sigue pendiente para una ruta posterior

#### Scenario: Admin asigna una reprogramada a otro chofer
- **WHEN** el admin arma una ruta para un chofer distinto del que falló la entrega y la deja marcada
- **THEN** la entrega queda incluida en la ruta de ese otro chofer
