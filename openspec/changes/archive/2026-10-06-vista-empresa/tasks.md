## 1. Etapa 1: shell compartido

- [x] 1.1 Extraer `componentes/escritorio/ShellEscritorio.tsx` de `EscritorioChofer.tsx` (sidebar, drawer, header, logo, banner de conexión y nav desde una lista de secciones); verificar con `npm run build` y en el navegador que el chofer independiente se ve igual en escritorio y en celular
- [x] 1.2 Hacer que `EscritorioChofer` derive las secciones y los permisos de `usuario.empresa_id` (sin Lugares para el chofer de empresa; `PanelVehiculo` en solo lectura; sin armar, editar ni cancelar en `RutaDeHoyEscritorio`); verificar en el navegador con un chofer de empresa de prueba
- [x] 1.3 Convertir `Inicio.tsx` en un despachador por rol y borrar `PestanaInicio.tsx`, `PanelPerfil.tsx` y `PanelChoferIndependiente.tsx`; verificar con `npm run build`, `npm run lint` y que no quede ninguna referencia (`grep`)

## 2. Etapa 1: choferes e invitaciones

- [x] 2.1 Backend: `GET /api/v1/empresa/choferes` en un router nuevo `api/routes_empresa.py` con `requiere_admin`, vehículo y resumen de hoy en una query; verificar con tests (flota propia, aislamiento entre empresas, 403 para choferes)
- [x] 2.2 Frontend: `EscritorioEmpresa` sobre `ShellEscritorio` con las secciones del admin, más `PanelChoferes` (lista + generar y copiar invitaciones con `/auth/invitaciones`); verificar en el navegador con un admin de prueba, en escritorio y en celular

## 3. Etapa 1: libreta de la empresa

- [x] 3.1 Backend: dependencia `requiere_planificador` (antes pensada como `requiere_gestor_de_libreta`) en la escritura de clientes y depósitos (403 para chofer de empresa); verificar con tests nuevos y que `test_clientes.py` y `test_depositos.py` siguen pasando
- [x] 3.2 Frontend: sección Lugares del admin reutilizando `PestanaLugares`; verificar en el navegador alta, edición y baja de un lugar y de un depósito como admin
- [x] 3.3 Cierre de etapa: `uv run pytest`, ruff, `npm run build`, `npm run lint` y `npm test` en verde; verificar que la etapa se puede desplegar sola

## 4. Etapa 2: asignación de rutas (backend)

- [x] 4.1 Agregar `requiere_chofer` y la función que resuelve el chofer destino (decisión 2 del diseño), y `chofer_id` opcional en los schemas de optimizar, confirmar y editar; `crud.crear_ruta` con `creado_por`; verificar con tests de cada rol (independiente sin `chofer_id`, admin con `chofer_id` propio, ajeno, sin vehículo y faltante, chofer de empresa 403)
- [x] 4.2 Reemplazar `_ruta_propia_o_404` por `crud.obtener_ruta_gestionable` (y `crud.obtener_ruta_de_empresa` para el detalle de la flota) con la condición en el `WHERE`; abrir a `requiere_chofer` los endpoints de ejecución, iniciar, rutas del día e historial propio; verificar con tests de admin editando y cancelando rutas de su flota y de otra empresa, y del chofer de empresa ejecutando una ruta asignada de punta a punta
- [x] 4.3 `fallar` con `reprogramar=true` desde un chofer de empresa responde 403; verificar con test

## 5. Etapa 2: entregas reprogramadas de la empresa

- [x] 5.1 `EntregaPendiente` con `DuenioMixin` y su `CHECK`; migración revisada a mano con downgrade explícito; verificar `upgrade` / `downgrade` / `upgrade` en la DB local
- [x] 5.2 Reprogramar con el `ambito_dueño` del chofer de la ruta; listar e incluir por `Duenio`; `GET /entregas-pendientes` para independiente y admin (403 para chofer de empresa); verificar con tests (admin ve las de varios choferes, admin incluye una en la ruta de otro chofer) y que `test_entregas_pendientes.py` sigue pasando sin cambios

## 6. Etapa 2: asignación y ejecución (frontend)

- [x] 6.1 Sección Armar ruta del admin: `FlujoArmarRuta` con selector de chofer y `chofer_id` en las llamadas; verificar en el navegador una ruta asignada y el error de capacidad
- [x] 6.2 Chofer de empresa: "Mis rutas" con las rutas asignadas e iniciar y ejecutar con `VistaEnCursoRuta` sin la opción de reprogramar; verificar en el navegador una ruta asignada de punta a punta hasta el resumen de cierre
- [x] 6.3 Cierre de etapa: suite completa y checks del frontend en verde

## 7. Etapa 3: seguimiento de la flota

- [x] 7.1 Backend: `GET /empresa/rutas?fecha=`, `GET /empresa/rutas/{id}`, `GET /empresa/rutas/{id}/geometria` y `GET /empresa/historial` con filtro de chofer; verificar con tests de alcance por empresa y 404 ajeno
- [x] 7.2 Backend: incidencias por alcance (`chofer_nombre` en `IncidenciaPublica`, listado del admin con `joinedload`, resolver por admin, 403 al chofer de empresa); verificar con tests y que `test_incidencias.py` sigue pasando
- [x] 7.3 Frontend: `PanelFlotaHoy` con polling de 30 s solo con la pestaña visible, más el detalle con paradas y mapa sin GPS; verificar en el navegador que el avance cambia al completar una parada desde otra sesión de chofer
- [x] 7.4 Frontend: Historial con filtro de chofer e Incidencias del admin con el nombre del chofer y resolución; verificar en el navegador
- [x] 7.5 Cierre de etapa: suite completa y checks del frontend en verde

## 8. Documentación

- [x] 8.1 Actualizar CLAUDE.md (§3 archivos, §9 quitar el gap de la vista clásica y sumar el de "sin posición en vivo", §10 roles y endpoints de empresa, §11 permisos por rol) y README si cambia algo de despliegue; verificar releyendo contra lo implementado
