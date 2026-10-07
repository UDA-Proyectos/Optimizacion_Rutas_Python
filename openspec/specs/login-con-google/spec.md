# login-con-google Specification

## Purpose
Permite entrar a la app y registrarse como chofer independiente con una cuenta de Google, sin crear ni recordar una contraseña propia, reutilizando la misma sesión por cookie que el login con email.

## Requirements

### Requirement: Disponibilidad según configuración
El sistema SHALL informar públicamente si el inicio de sesión con Google está habilitado, y lo SHALL considerar habilitado solo cuando el identificador y el secreto del cliente de Google están configurados. Con Google deshabilitado, el resto de la autenticación MUST seguir funcionando igual.

#### Scenario: Google configurado
- **WHEN** el identificador y el secreto del cliente de Google están configurados y se consultan los proveedores disponibles
- **THEN** el sistema informa que Google está habilitado

#### Scenario: Google sin configurar
- **WHEN** falta el identificador o el secreto del cliente de Google
- **THEN** el sistema informa que Google no está habilitado, el frontend no muestra el botón "Continuar con Google", y pedir el inicio del flujo de Google redirige al login con un error de "no disponible"

### Requirement: Iniciar el flujo con Google
El sistema SHALL iniciar el flujo redirigiendo el navegador a la pantalla de consentimiento de Google, pidiendo solo identidad básica (OpenID, email y perfil). Además SHALL asociar al navegador un valor de estado de un solo uso y corta duración, para validar la vuelta.

#### Scenario: Inicio del flujo
- **WHEN** un visitante toca "Continuar con Google" en Login o en Registro
- **THEN** el navegador es redirigido a Google con el estado de un solo uso, y Google le permite elegir la cuenta

### Requirement: Validar la vuelta desde Google
Al volver de Google, el sistema SHALL aceptar la respuesta solo si el estado coincide con el que se asoció al navegador. Además SHALL obtener la identidad del usuario directamente de Google y verificar que esa identidad fue emitida por Google, para esta aplicación, y que no está vencida. Cualquier fallo MUST terminar en el login con un mensaje de error, sin crear sesión ni exponer detalles internos.

#### Scenario: Estado ausente o distinto
- **WHEN** la vuelta desde Google trae un estado que no coincide con el del navegador, o el navegador no tiene estado
- **THEN** el sistema no inicia sesión y redirige al login con un error

#### Scenario: El usuario cancela en Google
- **WHEN** el usuario rechaza el consentimiento y Google vuelve con un error
- **THEN** el sistema redirige al login con un mensaje de que se canceló el ingreso con Google

#### Scenario: Google no responde o rechaza el código
- **WHEN** el canje del código con Google falla
- **THEN** el sistema redirige al login con un error genérico de Google y registra el detalle solo en el log del servidor

#### Scenario: Email no verificado por Google
- **WHEN** Google informa que el email de la cuenta no está verificado
- **THEN** el sistema no inicia sesión ni vincula cuentas, y redirige al login con un error

### Requirement: Ingreso con una cuenta existente
El sistema SHALL iniciar sesión, con la misma cookie de sesión que el login con email y contraseña, cuando la cuenta de Google ya está vinculada a un usuario o cuando su email verificado coincide con un usuario existente, sin importar el rol. En el segundo caso SHALL vincular la cuenta de Google a ese usuario para los próximos ingresos. Un usuario inactivo MUST NOT poder entrar.

#### Scenario: Cuenta de Google ya vinculada
- **WHEN** vuelve de Google una identidad ya vinculada a un usuario activo
- **THEN** el sistema inicia sesión con ese usuario y redirige al inicio de la app

#### Scenario: Email coincide con una cuenta creada con contraseña
- **WHEN** vuelve de Google un email verificado que coincide con un usuario activo todavía no vinculado
- **THEN** el sistema vincula la cuenta de Google a ese usuario, inicia sesión y redirige al inicio, y el usuario puede seguir entrando también con su contraseña

#### Scenario: Usuario inactivo
- **WHEN** la identidad de Google corresponde a un usuario inactivo
- **THEN** el sistema no inicia sesión y redirige al login con el error de cuenta inactiva

#### Scenario: Cuenta ya vinculada a otra identidad de Google
- **WHEN** el email coincide con un usuario que ya está vinculado a otra cuenta de Google
- **THEN** el sistema no inicia sesión ni cambia el vínculo, y redirige al login con un error

### Requirement: Registro de chofer independiente con Google
Cuando el email verificado de Google no corresponde a ningún usuario, el sistema SHALL pedir los datos que el registro de chofer independiente exige y Google no provee (teléfono, tipo de vehículo, patente y capacidad de carga) antes de crear la cuenta. La cuenta MUST NOT crearse hasta que esos datos se envíen y validen. Entre la vuelta de Google y ese envío, la identidad de Google SHALL quedar en el navegador en forma firmada, de corta duración y no legible por scripts.

#### Scenario: Primer ingreso con Google
- **WHEN** vuelve de Google un email verificado que no corresponde a ningún usuario
- **THEN** el sistema no crea ninguna cuenta y redirige a la pantalla de completar registro, que muestra el nombre y el email de Google sin permitir editar el email

#### Scenario: Completar el registro
- **WHEN** el visitante con un registro de Google pendiente envía nombre completo (precargado desde Google y editable), teléfono, tipo de vehículo, patente y capacidad válidos
- **THEN** el sistema crea un chofer independiente sin contraseña, vinculado a esa cuenta de Google, con su vehículo; inicia sesión y descarta el registro pendiente

#### Scenario: Datos del vehículo inválidos o patente duplicada
- **WHEN** los datos enviados no cumplen las mismas reglas que el registro con email, o la patente ya está registrada
- **THEN** el sistema responde con el mismo error que el registro con email (422 o 409) y no crea la cuenta

#### Scenario: Registro pendiente vencido o ausente
- **WHEN** se consulta o se completa el registro sin un registro de Google pendiente válido
- **THEN** el sistema responde 401 y el frontend vuelve al login pidiendo empezar de nuevo con Google

#### Scenario: El email se registró mientras tanto
- **WHEN** al completar el registro ya existe un usuario con ese email
- **THEN** el sistema responde 409 y no crea una segunda cuenta

### Requirement: Cuentas sin contraseña
Un usuario creado con Google SHALL NOT tener contraseña. El login con email y contraseña MUST rechazar a esos usuarios con el mismo error que un dato incorrecto. Los datos públicos del usuario SHALL indicar si tiene contraseña.

#### Scenario: Login con contraseña en una cuenta creada con Google
- **WHEN** alguien intenta entrar con email y contraseña a una cuenta que no tiene contraseña
- **THEN** el sistema responde 401 con "Email o contraseña incorrectos."

#### Scenario: Indicador en el perfil
- **WHEN** un usuario consulta sus datos
- **THEN** la respuesta indica si la cuenta tiene contraseña, y "Mi cuenta" oculta el cambio de contraseña cuando no tiene
