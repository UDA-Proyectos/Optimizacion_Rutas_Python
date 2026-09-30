## Purpose

Permite al chofer independiente mantener actualizados sus datos personales, los de su vehículo y su contraseña sin asistencia externa.

## ADDED Requirements

### Requirement: Editar perfil propio
El sistema SHALL permitir al usuario autenticado modificar su nombre completo y su teléfono, y SHALL devolver el usuario actualizado.

#### Scenario: Cambio de teléfono
- **WHEN** el chofer envía un teléfono válido nuevo
- **THEN** el sistema lo guarda y `GET /me` devuelve el valor nuevo

#### Scenario: Nombre vacío
- **WHEN** el chofer envía un nombre completo vacío
- **THEN** el sistema responde 422 y no modifica el perfil

#### Scenario: Email no editable
- **WHEN** el chofer incluye un email en la edición del perfil
- **THEN** el sistema ignora ese campo y el email no cambia

### Requirement: Editar vehículo propio
El sistema SHALL permitir al chofer independiente modificar el tipo, la patente y la capacidad de carga de su vehículo, y SHALL garantizar que la patente siga siendo única.

#### Scenario: Cambio de capacidad sin ruta activa
- **WHEN** el chofer sin ruta planificada ni en curso cambia la capacidad a 300 kg
- **THEN** el vehículo se actualiza y las próximas planificaciones usan 300 kg

#### Scenario: Patente duplicada
- **WHEN** el chofer usa la patente de otro vehículo
- **THEN** el sistema responde 409 y no modifica el vehículo

#### Scenario: Ruta activa
- **WHEN** el chofer intenta cambiar la capacidad o la patente con una ruta planificada o en curso
- **THEN** el sistema responde 409 indicando que debe terminar o cancelar la ruta

#### Scenario: Capacidad inválida
- **WHEN** el chofer envía una capacidad menor o igual a 0
- **THEN** el sistema responde 422

### Requirement: Cambiar contraseña
El sistema SHALL permitir cambiar la contraseña exigiendo la contraseña actual y confirmando la nueva, aplicando las mismas reglas de complejidad que el registro.

#### Scenario: Cambio correcto
- **WHEN** el chofer envía la contraseña actual correcta y una nueva válida confirmada
- **THEN** el sistema actualiza el hash y el chofer puede iniciar sesión solo con la nueva

#### Scenario: Contraseña actual incorrecta
- **WHEN** el chofer envía una contraseña actual incorrecta
- **THEN** el sistema responde 400 y no cambia la contraseña

#### Scenario: Confirmación distinta
- **WHEN** la nueva contraseña y su confirmación no coinciden
- **THEN** el sistema responde 422

### Requirement: Alcance por usuario
El sistema SHALL aplicar estas ediciones únicamente sobre los datos del usuario autenticado.

#### Scenario: Sin sesión
- **WHEN** se llama a cualquiera de estos endpoints sin sesión válida
- **THEN** el sistema responde 401
