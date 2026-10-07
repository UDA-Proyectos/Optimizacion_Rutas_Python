## Context

- **Frontend:** `paginas/Inicio.tsx` decide la pantalla. El chofer independiente va a `EscritorioChofer.tsx` (387 líneas: shell con sidebar/drawer/header, más el estado y las secciones del chofer). Admin y chofer de empresa caen en la vista clásica (`PestanaInicio.tsx` + `PanelPerfil.tsx`).
- **Backend:** clientes y depósitos ya se filtran por `Usuario.ambito_dueño` (empresa o chofer), así que la libreta de empresa existe. Rutas, incidencias, entregas pendientes y la edición del vehículo usan `requiere_chofer_independiente`. `Ruta` ya separa `chofer_id` de `creado_por_usuario_id`. `routing/planificador.planificar_ruta(db, usuario, ...)` toma el vehículo de `usuario.vehiculo` y los lugares de `usuario.ambito_dueño`. `EntregaPendiente` tiene solo `usuario_id`.
- Motivación y alcance: ver `proposal.md`. Comportamiento: ver los specs.

## Goals / Non-Goals

**Goals:**
- Un solo shell visual para los tres roles, sin duplicar el layout.
- Reutilizar el armado, la ejecución, el historial y las incidencias que ya existen, con permisos por rol, en lugar de crear versiones paralelas "de empresa".
- Que el chofer independiente no note ningún cambio, y que sus tests sigan pasando sin modificarse.

**Non-Goals:**
- Posición en vivo de los choferes. La ubicación nunca sale del dispositivo, y eso no cambia.
- Tiempo real con WebSockets o SSE. El seguimiento se refresca por polling.
- Gestión de vehículos por el admin, desactivar choferes, roles intermedios.

## Decisions

**1. Planificar para otro chofer = llamar al planificador con ese chofer.**
`planificar_ruta(db, chofer, ...)` ya hace lo correcto con un chofer de empresa: su `vehiculo` y su `ambito_dueño` (la empresa). El admin no necesita otro planificador: se resuelve el chofer destino y se le pasa. `crud.crear_ruta` suma `creado_por: Usuario` (hoy usa `chofer.id` para ambos).
- *Alternativa descartada:* un planificador "de empresa" que reciba el vehículo aparte. Duplica validaciones de capacidad y depósito.

**2. Los mismos endpoints de `/rutas` para armar, con `chofer_id` opcional.**
`OptimizarRutaRequest` (y por extensión confirmar y editar) suma `chofer_id: UUID | None`. Una sola función resuelve "para quién se planifica":
- Chofer independiente: `chofer_id` tiene que venir vacío, y el destino es él mismo.
- Admin: `chofer_id` es obligatorio (422 si falta) y tiene que ser un chofer de su empresa (404 si no; 409 si no tiene vehículo o está inactivo).
- Chofer de empresa: 403.

Así `FlujoArmarRuta` y todo el pipeline (preview, confirmar, editar) se reutilizan; el admin solo agrega un selector de chofer.
- *Alternativa descartada:* `/empresa/rutas/optimizar` y compañía. Duplicaría 4 endpoints y obligaría a parametrizar el cliente HTTP del flujo.

**3. Una regla de acceso a rutas por rol, en un solo lugar.**
Hoy hay `_ruta_propia_o_404`. Pasa a haber dos helpers en `api/routes_rutas.py`, respaldados por queries en `crud` que llevan la condición dentro del `WHERE` (mismo criterio que `_condicion_dueño`):
- `crud.obtener_ruta_gestionable(usuario, id)` (en `crud`, junto a `_incidencias_visibles`: el alcance por rol vive en un solo lugar; el router solo traduce `None` a 404), para editar y cancelar: chofer independiente → `chofer_id == usuario.id`; admin → `chofer.empresa_id == usuario.empresa_id`; chofer de empresa → 403 antes de buscar.
- El chofer (independiente o de empresa) sigue viendo solo las suyas con `_ruta_propia_o_404` (iniciar, historial). El detalle y la traza de una ruta de la flota para el admin viven en `routes_empresa` con `crud.obtener_ruta_de_empresa` (misma condición en el `WHERE`).

**4. Dependencias por capacidad, no por rol suelto.**
En `api/dependencies.py`:
- `requiere_chofer`: cualquier chofer (independiente o de empresa). Para ejecutar, iniciar, `GET /rutas?fecha=`, historial propio y reportar incidencias.
- `requiere_admin`: ya existe.
- `requiere_chofer_independiente`: se mantiene donde la regla es "solo el independiente", como `PATCH /me/vehiculo`.
- `requiere_planificador`: chofer independiente o admin, es decir, quien arma rutas y gestiona la libreta. Para optimizar, confirmar, editar y cancelar rutas, escribir clientes y depósitos, listar entregas pendientes y resolver incidencias. Al implementarlo quedó claro que "quien escribe la libreta" y "quien planifica" son el mismo conjunto, así que es una sola dependencia.

La diferencia entre el chofer independiente y el admin la deciden la función de la decisión 2 (para quién se planifica) y las consultas por alcance de la 7.

**5. Router nuevo `api/routes_empresa.py` (prefijo `/api/v1/empresa`, todo con `requiere_admin`), solo para lo que no tiene equivalente en el chofer:**
- `GET /choferes`: choferes de la empresa con vehículo y resumen de hoy (cantidad de rutas y si hay una en curso), resuelto en una query con agregados para evitar N+1.
- `GET /rutas?fecha=`: rutas de la flota en esa fecha, con el chofer y el avance. El avance sale del `RutaPublica` existente (paradas con estado), sin campos nuevos de persistencia.
- `GET /rutas/{id}` y `GET /rutas/{id}/geometria`: detalle y traza (reutilizan `obtener_geometria_osrm`).
- `GET /historial?desde&hasta&chofer_id=`.

Las invitaciones siguen en `/auth/invitaciones` (ya existen). `GET /incidencias` y `GET /entregas-pendientes` amplían su alcance según el rol (decisiones 6 y 7) en lugar de duplicarse.

**6. `EntregaPendiente` pasa a usar `DuenioMixin`.**
Migración: se agrega `empresa_id` nullable, `usuario_id` pasa a nullable y se agrega un `CHECK (num_nonnulls(empresa_id, usuario_id) = 1)`. Las filas existentes quedan con su `usuario_id` (todas son de choferes independientes). Al reprogramar se usa el `ambito_dueño` del chofer de la ruta. `listar_entregas_pendientes` y `marcar_entregas_incluidas` pasan a filtrar por `Duenio` con `_condicion_dueño`, igual que `Cliente`. Con eso, el admin ve las de su empresa sin código especial.

**7. Incidencias: listar y resolver por alcance.**
- `crud.listar_incidencias(db, alcance)`: chofer → las de sus rutas; admin → las de rutas cuyo chofer es de su empresa (join `Ruta → Usuario`, con `joinedload` para no reintroducir el N+1 ya corregido).
- `IncidenciaPublica` suma `chofer_nombre`.
- Resolver: chofer independiente (las suyas) o admin (las de su flota); chofer de empresa → 403.
- `fallar` con `reprogramar=true` desde un chofer de empresa → 403. El frontend no le ofrece la opción.

**8. Frontend: extraer el shell y declarar las secciones como datos.**
- `componentes/escritorio/ShellEscritorio.tsx`: sidebar, drawer, header, logo, banner de conexión y nav. Recibe `secciones: { id, etiqueta, icono, grupo, badge? }[]`, la sección actual y el contenido. Sale casi literal de `EscritorioChofer.tsx`, que queda con el estado y las secciones del chofer.
- `EscritorioChofer` sirve a los dos tipos de chofer. Deriva `const esIndependiente = usuario.empresa_id === null` una sola vez y arma su lista de secciones y sus permisos (`puedePlanificar`, `editable` del vehículo, `puedeReprogramar` y el `alcance` de incidencias: `propias` o `deEmpresa`; el admin usa `flota`) a partir de eso. Esos permisos van como props a `RutaDeHoyEscritorio`, `PanelVehiculo`, `PanelIncidencias` y `VistaEnCursoRuta` (que oculta la opción de reprogramar).
- `EscritorioEmpresa` (admin): Hoy (`PanelFlotaHoy` con polling de 30 s mientras la pestaña es visible, más el detalle de ruta reutilizando la lista de paradas y `MapaRutaActiva` sin GPS), Armar ruta (`FlujoArmarRuta` + selector de chofer), Choferes (`PanelChoferes` + invitaciones), Lugares (`PestanaLugares`), Historial (`PanelHistorial` con filtro de chofer), Incidencias (`PanelIncidencias` con el chofer) y Mi cuenta (`PanelCuenta`).
- `Inicio.tsx` queda como un despachador de 3 ramas. Se borran `PestanaInicio.tsx`, `PanelPerfil.tsx` y `PanelChoferIndependiente.tsx` (un wrapper sin lógica).
- *Alternativa descartada:* copiar `EscritorioChofer` como `EscritorioEmpresa`. Dos layouts que divergen con el tiempo.

**9. Modo offline.**
Se mantiene igual para cualquier chofer: `useRutasDelDia` ya guarda las rutas del día y la en curso, y no depende del rol. (`useRutaActiva` solo lo usaba la vista clásica: se borró junto con ella, y su tipo `EjecutarAccionRuta` pasó a `useRutasDelDia`.) El escritorio del admin no tiene modo offline: sin conexión muestra el `BannerConexion` y bloquea las escrituras como el resto.

## Risks / Trade-offs

- [El `chofer_id` opcional en `/rutas` mezcla dos actores en un endpoint] → La regla vive en una sola función con tests por rol. Es más simple que dos juegos de endpoints que hay que mantener iguales.
- [Polling cada 30 s con muchos choferes] → Una sola query con `selectinload` de paradas por fecha. Si la flota crece, se puede bajar a un endpoint de resumen sin paradas.
- [Cambiar `EntregaPendiente` a dueño mixto toca un flujo ya archivado] → Las filas existentes no cambian. Los tests actuales de entregas reprogramadas cubren al chofer independiente y tienen que seguir pasando sin cambios.
- [Restringir la escritura de la libreta al admin puede romper a un chofer de empresa que hoy la usa por API] → Hoy no hay UI para eso. Se documenta en CLAUDE.md.
- [Extraer el shell puede romper estilos del chofer independiente] → Es un movimiento casi literal. Se verifica en el navegador en escritorio y en celular antes de seguir.

## Migration Plan

1. **Etapa 1** se despliega sin migración: el shell, los choferes, las invitaciones y la libreta del admin.
2. **Etapa 2** incluye la migración de `EntregaPendiente`. Railway corre `alembic upgrade head` al arrancar. El downgrade falla explícitamente si hay entregas con dueño empresa.
3. **Etapa 3** no tiene migraciones.
4. Rollback de cualquier etapa: volver al commit anterior. Los datos nuevos (rutas asignadas por admin) siguen siendo rutas válidas para el chofer.

## Open Questions

- El intervalo de refresco de "Hoy" (30 s) se puede ajustar después de probarlo con datos reales. No cambia el diseño.
