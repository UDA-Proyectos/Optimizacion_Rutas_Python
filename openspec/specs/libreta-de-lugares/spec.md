# libreta-de-lugares Specification

## Purpose
Permite guardar en la libreta de lugares los datos habituales de cada cliente y del depósito, para no reingresarlos en cada ruta y para que la planificación con ventanas horarias use tiempos realistas.

## Requirements

### Requirement: Datos habituales del lugar
El sistema SHALL permitir guardar por cada lugar una carga habitual (kg), un tiempo de servicio en minutos (0 por defecto) y una ventana horaria habitual, y SHALL devolverlos al consultar el lugar.

#### Scenario: Alta con datos habituales
- **WHEN** el chofer crea un lugar con carga 20 kg, servicio 10 min y ventana 09:00–12:00
- **THEN** el lugar se guarda con esos valores y los devuelve al listarlo

#### Scenario: Ventana inválida
- **WHEN** el chofer guarda una ventana cuyo fin es anterior o igual al inicio
- **THEN** el sistema responde 422 y no guarda el lugar

#### Scenario: Servicio fuera de rango
- **WHEN** el chofer guarda un tiempo de servicio negativo o mayor a 240 minutos
- **THEN** el sistema responde 422

### Requirement: Precarga al armar la ruta
El sistema SHALL precargar, al seleccionar un lugar para la ruta del día, su carga y ventana habituales, y SHALL permitir modificarlos para esa ruta sin alterar el lugar.

#### Scenario: Lugar con valores habituales
- **WHEN** el chofer selecciona un lugar que tiene carga y ventana habituales
- **THEN** los campos de la parada aparecen completados con esos valores

#### Scenario: Cambio puntual
- **WHEN** el chofer cambia la carga de esa parada para hoy
- **THEN** la ruta usa el valor de hoy y el lugar conserva su carga habitual

### Requirement: Tiempo de servicio en la planificación
El sistema SHALL usar el tiempo de servicio de cada lugar al planificar con ventanas horarias, de modo que los horarios estimados de llegada lo incluyan.

#### Scenario: ETA con servicio
- **WHEN** el chofer planifica con ventanas horarias dos paradas consecutivas, la primera con servicio de 15 minutos
- **THEN** la llegada estimada a la segunda incluye esos 15 minutos además del traslado

### Requirement: Ventana horaria del depósito
El sistema SHALL permitir configurar la ventana horaria del depósito y SHALL respetarla al planificar con ventanas horarias.

#### Scenario: Ventana del depósito acota la ruta
- **WHEN** el depósito abre a las 08:00 y cierra a las 18:00 y la ruta con ventanas no puede volver antes de las 18:00
- **THEN** la planificación falla con un mensaje que indica revisar las ventanas horarias

### Requirement: Depósito de salida elegible
El sistema SHALL permitir elegir, al planificar, cuál de los depósitos activos del chofer es el punto de partida y llegada, y SHALL usar el primero cuando no se elige ninguno.

#### Scenario: Depósito elegido
- **WHEN** el chofer con dos depósitos elige el segundo al optimizar
- **THEN** la ruta parte y termina en ese depósito

#### Scenario: Depósito ajeno
- **WHEN** el chofer envía el identificador de un depósito que no le pertenece
- **THEN** el sistema responde 400 y no planifica

### Requirement: Lugares y depósitos de una empresa
En una empresa, los lugares y depósitos SHALL ser compartidos por toda la flota, y solo el admin SHALL poder crearlos, editarlos o darlos de baja. El chofer independiente mantiene su propia libreta sin cambios.

#### Scenario: Admin gestiona la libreta
- **WHEN** el admin crea, edita o da de baja un lugar o un depósito
- **THEN** el cambio queda en la libreta de la empresa y se ve al armar rutas para cualquier chofer de esa empresa

#### Scenario: Chofer de empresa intenta escribir
- **WHEN** un chofer de empresa intenta crear, editar o dar de baja un lugar o un depósito
- **THEN** el sistema responde 403 y la libreta no cambia
