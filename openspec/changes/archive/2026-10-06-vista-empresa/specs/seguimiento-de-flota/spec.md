## Purpose

Le da al admin de una empresa visibilidad sobre cómo avanza su flota durante el día y sobre lo que pasó después, con el historial y las incidencias de todos sus choferes en un solo lugar.

## ADDED Requirements

### Requirement: Avance del día de la flota
El sistema SHALL mostrar al admin, para una fecha, las rutas no canceladas de todos los choferes de su empresa con su estado y su avance (paradas completadas, fallidas, salteadas, pendientes y la parada en curso), y la pantalla SHALL refrescarse sola mientras está abierta.

#### Scenario: Día con rutas en curso
- **WHEN** el admin abre "Hoy" y hay choferes con rutas en curso
- **THEN** ve cada ruta con su chofer, estado, cantidad de paradas hechas sobre el total y la parada actual

#### Scenario: Actualización sin recargar
- **WHEN** un chofer completa una parada mientras el admin tiene "Hoy" abierto
- **THEN** el avance se actualiza solo en el siguiente refresco, sin recargar la página

#### Scenario: Otra fecha
- **WHEN** el admin cambia de día
- **THEN** ve las rutas de la flota para ese día

### Requirement: Detalle de una ruta de la flota
El sistema SHALL permitir al admin abrir el detalle de cualquier ruta de su flota con sus paradas, su estado, la traza en el mapa y, si está completada, el resumen de cierre. El mapa MUST NOT mostrar la posición en vivo del chofer.

#### Scenario: Abrir detalle
- **WHEN** el admin abre una ruta de la flota
- **THEN** ve sus paradas en orden con su estado y la traza en el mapa

#### Scenario: Ruta de otra empresa
- **WHEN** el admin pide el detalle de una ruta de otra empresa
- **THEN** el sistema responde 404

### Requirement: Historial de la flota
El sistema SHALL mostrar al admin el historial de rutas de toda su empresa en un rango de fechas, con el chofer de cada una, y SHALL permitir filtrarlo por chofer.

#### Scenario: Historial filtrado
- **WHEN** el admin filtra el historial por un chofer
- **THEN** ve solo las rutas de ese chofer en el rango elegido

### Requirement: Incidencias de la flota
El sistema SHALL listar al admin las incidencias de todas las rutas de su empresa, con el nombre del chofer que la reportó, filtrables por estado.

#### Scenario: Incidencias de varios choferes
- **WHEN** el admin consulta las incidencias pendientes
- **THEN** recibe las de todos los choferes de su empresa, cada una con el nombre del chofer

#### Scenario: Aislamiento entre empresas
- **WHEN** existen incidencias de otra empresa
- **THEN** no aparecen en el listado del admin
