## Purpose

Define qué escritorio y qué secciones ve cada rol de la app (chofer independiente, chofer de empresa y admin de empresa), todos con el mismo shell visual, para que ninguno quede en una pantalla con otro estilo o con funciones que no le corresponden.

## ADDED Requirements

### Requirement: Mismo shell visual para todos los roles
El sistema SHALL mostrar a todo usuario autenticado el mismo shell de escritorio que usa hoy el chofer independiente: menú lateral en pantallas anchas, menú desplegable en pantallas chicas, encabezado con la sección actual y el logo de la app. La vista clásica anterior MUST dejar de existir.

#### Scenario: Admin entra a la app
- **WHEN** un admin de empresa inicia sesión
- **THEN** ve el shell de escritorio con las secciones de empresa, no la pantalla clásica de saludo

#### Scenario: Chofer de empresa entra a la app
- **WHEN** un chofer de empresa inicia sesión
- **THEN** ve el shell de escritorio con las secciones de chofer de empresa

#### Scenario: Pantalla chica
- **WHEN** cualquier rol usa la app en un ancho de celular
- **THEN** el menú se abre como desplegable y todas sus secciones son accesibles

### Requirement: Secciones por rol
El sistema SHALL ofrecer a cada rol solo las secciones que puede usar:
- Chofer independiente: Mis rutas, Mis lugares, Historial, Mi vehículo, Incidencias, Mi cuenta (sin cambios).
- Chofer de empresa: Mis rutas, Historial, Mi vehículo (solo lectura), Incidencias, Mi cuenta.
- Admin de empresa: Hoy, Armar ruta, Choferes, Lugares, Historial, Incidencias, Mi cuenta.

#### Scenario: Chofer de empresa sin libreta de lugares
- **WHEN** un chofer de empresa abre el menú
- **THEN** no aparece la sección de lugares ni ninguna acción para armar, editar o cancelar rutas

#### Scenario: Vehículo del chofer de empresa
- **WHEN** un chofer de empresa abre "Mi vehículo"
- **THEN** ve tipo, patente y capacidad sin la opción de editarlos

#### Scenario: Admin sin ejecución de rutas
- **WHEN** un admin navega su escritorio
- **THEN** no tiene acciones de ejecutar paradas (llegada, completar, fallar, saltear), solo de planificar y hacer seguimiento
