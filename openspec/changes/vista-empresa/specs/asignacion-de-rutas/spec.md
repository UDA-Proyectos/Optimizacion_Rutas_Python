## Purpose

Permite al admin de una empresa armar rutas optimizadas para los choferes de su flota con el mismo motor y flujo que usa el chofer independiente, y que cada chofer de empresa reciba y vea las rutas que le asignaron.

## ADDED Requirements

### Requirement: Armar y asignar una ruta
El sistema SHALL permitir al admin armar una ruta eligiendo el chofer de su empresa, la fecha, el nombre opcional, los lugares de la empresa con su carga y bultos, si usa ventanas horarias y el depósito de salida, con las mismas validaciones y el mismo preview que el armado del chofer independiente. La ruta MUST planificarse con la capacidad del vehículo del chofer elegido, quedar asignada a ese chofer y registrar al admin como quien la creó.

#### Scenario: Asignación correcta
- **WHEN** el admin confirma una ruta para un chofer de su empresa con vehículo
- **THEN** se crea una ruta planificada de ese chofer, con su vehículo, creada por el admin

#### Scenario: Capacidad del chofer elegido
- **WHEN** la carga total supera la capacidad del vehículo del chofer elegido
- **THEN** el sistema responde 400 con el mismo mensaje que en el armado propio y no crea la ruta

#### Scenario: Chofer de otra empresa
- **WHEN** el admin intenta asignar una ruta a un chofer que no es de su empresa
- **THEN** el sistema responde 404

#### Scenario: Chofer sin vehículo o inactivo
- **WHEN** el chofer elegido no tiene vehículo o está inactivo
- **THEN** el sistema responde 409 y no crea la ruta

#### Scenario: Sin chofer elegido
- **WHEN** el admin intenta armar una ruta sin indicar el chofer
- **THEN** el sistema responde 422

### Requirement: Editar y cancelar rutas de la flota
El sistema SHALL permitir al admin editar una ruta planificada de un chofer de su empresa (con las mismas reglas que la edición propia: se cancela la anterior y se crea una nueva) y cancelar una ruta planificada o en curso. MUST NOT permitirle tocar rutas de otras empresas.

#### Scenario: Editar ruta planificada
- **WHEN** el admin edita una ruta planificada de su flota
- **THEN** la ruta anterior queda cancelada y se crea la nueva para el mismo chofer, fecha y nombre

#### Scenario: Ruta de otra empresa
- **WHEN** el admin intenta editar o cancelar una ruta de un chofer de otra empresa
- **THEN** el sistema responde 404

### Requirement: Rutas asignadas al chofer de empresa
El sistema SHALL mostrar al chofer de empresa sus rutas de cada día, que le asignó su empresa, y SHALL permitirle elegir cuál iniciar con las mismas reglas que el chofer independiente: una sola en curso a la vez y solo el día de la ruta. El chofer de empresa MUST NOT poder armar, editar ni cancelar rutas.

#### Scenario: Ver rutas asignadas
- **WHEN** el chofer de empresa consulta las rutas de un día
- **THEN** ve las que le asignaron para ese día, con su nombre, paradas y estado

#### Scenario: Intento de armar una ruta
- **WHEN** un chofer de empresa intenta optimizar, confirmar, editar o cancelar una ruta
- **THEN** el sistema responde 403
