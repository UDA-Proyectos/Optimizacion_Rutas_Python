## Purpose

Permite al chofer independiente preparar rutas para hoy o para días futuros, tener varias el mismo día y elegir cuál realizar.

## ADDED Requirements

### Requirement: Planificar una ruta para una fecha
El sistema SHALL permitir armar y confirmar una ruta para una fecha indicada, que SHALL ser hoy o un día posterior dentro de los 60 días siguientes, y SHALL usar hoy cuando no se indica fecha. El sistema SHALL NOT permitir planificar para un día que ya pasó.

#### Scenario: Ruta para mañana
- **WHEN** el chofer confirma una ruta indicando la fecha de mañana
- **THEN** la ruta queda planificada con esa fecha

#### Scenario: Sin fecha
- **WHEN** el chofer confirma una ruta sin indicar fecha
- **THEN** la ruta queda planificada para hoy

#### Scenario: Fecha pasada
- **WHEN** el chofer intenta confirmar una ruta para una fecha anterior a ayer (se tolera un día de diferencia por zona horaria)
- **THEN** el sistema responde 400 y no crea la ruta

#### Scenario: Fecha demasiado lejana
- **WHEN** el chofer indica una fecha a más de 60 días
- **THEN** el sistema responde 400 y no crea la ruta

### Requirement: Varias rutas el mismo día
El sistema SHALL permitir tener varias rutas planificadas para el mismo día y SHALL permitir ponerle a cada una un nombre opcional para distinguirlas.

#### Scenario: Segunda ruta del día
- **WHEN** el chofer que ya tiene una ruta planificada para un día confirma otra para ese mismo día
- **THEN** ambas quedan planificadas y el sistema no responde 409

#### Scenario: Nombre demasiado largo
- **WHEN** el chofer indica un nombre de más de 60 caracteres
- **THEN** el sistema responde 422

### Requirement: Consultar las rutas de un día
El sistema SHALL listar las rutas del chofer para una fecha, incluyendo las planificadas, en curso y completadas y excluyendo las canceladas, en el orden en que se crearon, y SHALL usar hoy cuando no se indica fecha.

#### Scenario: Día con dos rutas
- **WHEN** el chofer consulta un día con dos rutas planificadas y una cancelada
- **THEN** recibe las dos planificadas en orden de creación

#### Scenario: Día sin rutas
- **WHEN** el chofer consulta un día sin rutas
- **THEN** recibe una lista vacía

### Requirement: Elegir cuál ruta iniciar
El sistema SHALL permitir iniciar una ruta planificada indicando cuál, y SHALL pasar la primera parada de esa ruta a en curso.

#### Scenario: Iniciar la segunda del día
- **WHEN** el chofer con dos rutas planificadas hoy inicia la segunda
- **THEN** esa ruta queda en curso y la otra sigue planificada

#### Scenario: Ruta ajena
- **WHEN** el chofer intenta iniciar una ruta de otro chofer
- **THEN** el sistema responde 404

### Requirement: Una sola ruta en curso
El sistema SHALL permitir una sola ruta en curso a la vez por chofer.

#### Scenario: Iniciar con otra en curso
- **WHEN** el chofer con una ruta en curso intenta iniciar otra
- **THEN** el sistema responde 409 indicando que debe terminar o cancelar la ruta en curso

#### Scenario: Ruta en curso de la consulta activa
- **WHEN** el chofer consulta su ruta en curso
- **THEN** recibe esa ruta, o nada si no tiene ninguna, sin importar su fecha

### Requirement: Iniciar solo el día de la ruta
El sistema SHALL permitir iniciar una ruta únicamente desde el día para el que fue planificada.

#### Scenario: Ruta de mañana
- **WHEN** el chofer intenta iniciar hoy una ruta planificada para mañana
- **THEN** el sistema responde 409 indicando la fecha de la ruta

### Requirement: Editar o cancelar una ruta concreta
El sistema SHALL permitir editar una ruta planificada, conservando su fecha y su nombre salvo que se indiquen otros, y SHALL permitir cancelar una ruta planificada o en curso, identificándola en cada caso.

#### Scenario: Editar una de dos
- **WHEN** el chofer edita la primera de sus dos rutas del día
- **THEN** solo esa ruta se reemplaza y la otra no cambia

#### Scenario: Editar una ruta en curso
- **WHEN** el chofer intenta editar una ruta que ya está en curso
- **THEN** el sistema responde 409

#### Scenario: Cancelar una ruta ya completada
- **WHEN** el chofer intenta cancelar una ruta completada
- **THEN** el sistema responde 409
