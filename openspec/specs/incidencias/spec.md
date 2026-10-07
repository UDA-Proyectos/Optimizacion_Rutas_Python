# incidencias Specification

## Purpose
Permite a cada chofer reportar problemas ocurridos durante su ruta y consultar lo que reportó, y resolverlos a quien corresponde: el chofer independiente las suyas, el admin las de su flota.

## Requirements

### Requirement: Reportar una incidencia
El sistema SHALL permitir al chofer independiente reportar una incidencia sobre su ruta en curso, indicando tipo y descripción opcional, y opcionalmente la parada afectada.

#### Scenario: Incidencia general de la ruta
- **WHEN** el chofer con una ruta en curso reporta una incidencia de tipo "problema de vehículo" sin parada
- **THEN** el sistema la guarda asociada a la ruta y al chofer, con fecha y hora actuales

#### Scenario: Incidencia sobre una parada
- **WHEN** el chofer reporta una incidencia indicando una parada de su ruta activa
- **THEN** el sistema la guarda asociada a esa parada

#### Scenario: Parada ajena
- **WHEN** el chofer indica una parada que no pertenece a su ruta activa
- **THEN** el sistema responde 404 y no crea la incidencia

#### Scenario: Sin ruta en curso
- **WHEN** el chofer intenta reportar una incidencia sin ruta en curso
- **THEN** el sistema responde 409 indicando que necesita iniciar una ruta

### Requirement: Tipos de incidencia válidos
El sistema SHALL aceptar únicamente los tipos: cliente ausente, rechazo de entrega, dirección incorrecta, mercadería dañada, problema de vehículo y otro.

#### Scenario: Tipo inválido
- **WHEN** el chofer envía un tipo que no está en la lista
- **THEN** el sistema responde 422

### Requirement: Consultar incidencias propias
El sistema SHALL listar las incidencias del chofer, ordenadas de la más reciente a la más antigua, incluyendo las generadas al marcar una parada como fallida, y SHALL mostrar solo las suyas.

#### Scenario: Listado propio
- **WHEN** el chofer consulta sus incidencias
- **THEN** recibe únicamente las que reportó él, con tipo, descripción, fecha, ruta y nombre de la parada si corresponde

#### Scenario: Sin incidencias
- **WHEN** el chofer no reportó ninguna
- **THEN** la respuesta es una lista vacía y la sección muestra un estado vacío

### Requirement: Estado de una incidencia
El sistema SHALL mantener para cada incidencia un estado, pendiente o resuelta, y, cuando está resuelta, su resolución (reprogramada o cerrada) y la fecha. Las incidencias generadas por una entrega fallida SHALL nacer pendientes; las incidencias generales de la ruta también, hasta que el chofer las cierre.

#### Scenario: Incidencia nueva
- **WHEN** se crea una incidencia
- **THEN** su estado es pendiente y no tiene resolución

### Requirement: Filtrar incidencias por estado
El sistema SHALL permitir listar las incidencias del chofer filtrando por estado pendiente o resuelta, y SHALL devolver todas cuando no se indica filtro.

#### Scenario: Solo pendientes
- **WHEN** el chofer pide las incidencias pendientes
- **THEN** recibe únicamente las que no fueron resueltas

#### Scenario: Estado inválido
- **WHEN** el chofer filtra por un estado que no existe
- **THEN** el sistema responde 422

### Requirement: Resolver una incidencia
El sistema SHALL permitir resolver una incidencia pendiente eligiendo entre reprogramar la entrega (solo si la incidencia proviene de una parada fallida) o cerrarla sin más acción, y SHALL registrar la resolución. El chofer independiente resuelve las suyas; en una empresa, las resuelve el admin, sobre cualquier incidencia de su flota, y el chofer de empresa MUST NOT resolverlas.

#### Scenario: Reprogramar desde una incidencia
- **WHEN** el chofer resuelve como reprogramada una incidencia pendiente de una parada fallida
- **THEN** la incidencia queda resuelta como reprogramada y la entrega queda pendiente para la próxima ruta

#### Scenario: Cerrar sin acción
- **WHEN** el chofer cierra una incidencia pendiente
- **THEN** queda resuelta como cerrada y no se crea ninguna entrega pendiente

#### Scenario: Reprogramar una incidencia sin parada fallida
- **WHEN** el chofer pide reprogramar una incidencia general o de una parada que no está fallida
- **THEN** el sistema responde 409 y la incidencia sigue pendiente

#### Scenario: Incidencia ya resuelta
- **WHEN** el chofer intenta resolver una incidencia que ya está resuelta
- **THEN** el sistema responde 409

#### Scenario: Incidencia ajena
- **WHEN** el chofer intenta resolver una incidencia de otro chofer
- **THEN** el sistema responde 404

#### Scenario: Admin resuelve una incidencia de su flota
- **WHEN** el admin resuelve como reprogramada una incidencia pendiente de una parada fallida de un chofer de su empresa
- **THEN** la incidencia queda resuelta y la entrega queda pendiente para la empresa

#### Scenario: Chofer de empresa intenta resolver
- **WHEN** un chofer de empresa intenta resolver una incidencia
- **THEN** el sistema responde 403 y la incidencia sigue pendiente

#### Scenario: Incidencia de otra empresa
- **WHEN** el admin intenta resolver una incidencia de otra empresa
- **THEN** el sistema responde 404

### Requirement: Incidencias del chofer de empresa
El sistema SHALL permitir al chofer de empresa reportar una incidencia sobre su ruta en curso y consultar las que reportó, con los mismos tipos, estados y filtros que el chofer independiente.

#### Scenario: Reportar durante la ruta
- **WHEN** el chofer de empresa reporta una incidencia con una ruta en curso
- **THEN** la incidencia queda pendiente, asociada a su ruta, y la ve el admin de su empresa

#### Scenario: Consultar las propias
- **WHEN** el chofer de empresa consulta sus incidencias
- **THEN** ve solo las de sus rutas, sin acciones para resolverlas
