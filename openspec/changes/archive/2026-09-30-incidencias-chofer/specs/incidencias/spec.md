## Purpose

Permite al chofer independiente reportar problemas ocurridos durante su ruta y consultar el historial de lo que reportó.

## ADDED Requirements

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
