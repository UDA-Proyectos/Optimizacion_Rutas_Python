## Why

El chofer independiente tiene un escritorio completo (menú lateral, rutas, lugares, historial, vehículo, incidencias, cuenta), pero el admin de empresa y el chofer de empresa todavía ven la pantalla "clásica": un saludo y una pestaña Inicio vieja que solo sabe completar paradas (CLAUDE.md §9). Una empresa no puede gestionar su flota desde la app: los códigos de invitación existen solo por API, nadie puede asignarle una ruta a un chofer de la empresa, y ese chofer no tiene forma de ejecutarla. Este cambio iguala la experiencia visual y le da a cada rol las funciones que le corresponden.

## What Changes

Se entrega por etapas; cada una se puede desplegar sola.

**Etapa 1: escritorio de empresa, choferes y lugares**
- El admin y el chofer de empresa usan el mismo shell responsive que el chofer independiente (sidebar violeta en escritorio, drawer en el celular), cada uno con sus propias secciones.
- **BREAKING (frontend):** se elimina la vista clásica (`Inicio` clásico, `PestanaInicio.tsx`, `PanelPerfil.tsx`).
- Admin → **Choferes**: lista de la flota (nombre, contacto, vehículo, estado de hoy), y generar y copiar códigos de invitación desde la UI.
- Admin → **Lugares**: la misma libreta de lugares y depósitos, compartida por toda la empresa.
- Escribir lugares y depósitos de una empresa queda reservado al admin. El chofer de empresa no ve esa sección.

**Etapa 2: asignación y ejecución de rutas**
- El admin arma una ruta con el mismo flujo que el chofer independiente, pero eligiendo a qué chofer se la asigna. La ruta se planifica con el vehículo de ese chofer y los lugares y depósitos de la empresa. También puede editar y cancelar rutas de su flota.
- El chofer de empresa ve sus rutas asignadas ("Mis rutas") y las ejecuta igual que el independiente: iniciar, llegada, completar, no pude entregar, saltear, incidencias y resumen de cierre. No arma, no edita ni cancela rutas, y ve su vehículo solo en modo lectura.
- Las entregas reprogramadas de una empresa pasan a ser de la empresa, no del chofer: el admin las ve al armar cualquier ruta.

**Etapa 3: seguimiento de la flota**
- Admin → **Hoy**: las rutas del día de todos los choferes con su avance (paradas hechas, fallidas, en curso), que se refresca solo, con el detalle y el mapa de cada ruta.
- Admin → **Historial** de toda la flota, filtrable por chofer.
- Admin → **Incidencias** de toda la empresa (con el nombre del chofer), que el admin resuelve. El chofer de empresa reporta y consulta las suyas, pero no las resuelve.

## Capabilities

### New Capabilities
- `escritorio-por-rol`: qué escritorio y qué secciones ve cada rol (chofer independiente, chofer de empresa, admin), con el mismo shell visual, reemplazando la vista clásica.
- `gestion-de-choferes`: el admin consulta los choferes de su empresa y genera y lista códigos de invitación desde la app.
- `asignacion-de-rutas`: el admin arma, asigna, edita y cancela rutas para los choferes de su empresa; el chofer de empresa las recibe.
- `seguimiento-de-flota`: el admin ve el avance del día, el historial y las incidencias de toda su flota.

### Modified Capabilities
- `ejecucion-de-ruta`: el chofer de empresa ejecuta sus rutas asignadas con las mismas reglas.
- `libreta-de-lugares`: en una empresa, solo el admin escribe lugares y depósitos.
- `incidencias`: el chofer de empresa reporta y consulta las suyas; en una empresa las resuelve el admin.
- `entregas-reprogramadas`: en una empresa, la entrega reprogramada pertenece a la empresa.
- `resumen-y-historial-de-ruta`: el chofer de empresa consulta el resumen y el historial de sus rutas.

## Impact

- **Backend:** `api/dependencies.py` (dependencias por rol), `api/routes_rutas.py` (rutas gestionables por el admin y ejecución por cualquier chofer), router nuevo `api/routes_empresa.py` (choferes, rutas y seguimiento de la flota), `api/routes_incidencias.py`, `api/routes_entregas_pendientes.py`, `api/routes_clientes.py` y `api/routes_depositos.py` (escritura solo admin en empresa), `db/crud.py`, `db/modelos.py`.
- **Base de datos:** migración para que `EntregaPendiente` tenga dueño empresa o chofer (como `Cliente`/`Deposito`). Las filas existentes no cambian de dueño.
- **Frontend:** se extrae el shell de `EscritorioChofer.tsx` a un componente reutilizable; nuevos `EscritorioEmpresa` y paneles de choferes y seguimiento; `FlujoArmarRuta`, `RutaDeHoyEscritorio`, `PanelHistorial`, `PanelIncidencias` y `PanelVehiculo` se reutilizan con permisos por rol. Se eliminan `Inicio` clásico, `PestanaInicio` y `PanelPerfil`.
- **Tests:** backend con choferes de empresa y admin (permisos, asignación, ejecución, alcance por empresa). Los tests del chofer independiente no deberían cambiar.
- **Fuera de alcance:** posición en vivo de los choferes (la ubicación del dispositivo nunca se envía al backend), alta de vehículos por el admin ("Mi flota"), desactivar o desvincular choferes, notificaciones push, prueba de entrega (POD), billing.
