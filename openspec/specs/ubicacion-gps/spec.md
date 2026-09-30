# ubicacion-gps Specification

## Purpose
Usa la posición del dispositivo del chofer, solo en el cliente, para mostrarla en el mapa y arrancar la navegación desde donde realmente está.

## Requirements

### Requirement: Permiso explícito
El sistema SHALL pedir la ubicación del dispositivo solo cuando el chofer lo solicita o activa la función, y SHALL funcionar completo si el permiso se deniega.

#### Scenario: Permiso denegado
- **WHEN** el chofer deniega el permiso de ubicación
- **THEN** la app sigue funcionando y la navegación usa como origen el depósito o la parada anterior

### Requirement: Posición en el mapa
El sistema SHALL mostrar la posición actual del chofer en el mapa de la ruta activa cuando el permiso está concedido.

#### Scenario: Posición disponible
- **WHEN** el chofer con permiso concedido abre el mapa de la ruta en curso
- **THEN** ve un marcador de su posición diferenciado de los pines de las paradas

### Requirement: Navegación desde la posición actual
El sistema SHALL usar la posición actual como origen del enlace "Ir con Maps" cuando está disponible, y SHALL usar el origen actual del tramo (depósito o parada anterior) en caso contrario.

#### Scenario: Con posición
- **WHEN** el chofer toca "Ir con Maps" con la posición conocida
- **THEN** el enlace usa su posición como origen y la parada actual como destino

#### Scenario: Sin posición
- **WHEN** el chofer toca "Ir con Maps" sin posición disponible
- **THEN** el enlace usa el origen del tramo como hasta ahora

### Requirement: La posición no sale del dispositivo
El sistema SHALL NOT enviar al servidor ni almacenar de forma persistente la posición del chofer.

#### Scenario: Sin tráfico de ubicación
- **WHEN** el chofer usa la app con el permiso concedido
- **THEN** ninguna solicitud al backend incluye su latitud o longitud actual
