# pwa-offline Specification

## Purpose
Hace que la aplicación del chofer sea instalable y siga siendo útil, en modo lectura, cuando el dispositivo pierde conexión durante la ruta.

## Requirements

### Requirement: Aplicación instalable
El sistema SHALL ofrecer un manifest de aplicación web con nombre, iconos, color de tema violeta y modo de visualización independiente, de modo que el navegador permita instalarla.

#### Scenario: Instalación
- **WHEN** el chofer abre la app en un navegador compatible sobre HTTPS
- **THEN** el navegador ofrece instalarla y, una vez instalada, se abre sin barra de direcciones

### Requirement: Arranque sin conexión
El sistema SHALL cachear los recursos estáticos de la app para que pueda abrirse sin conexión después de una primera carga exitosa.

#### Scenario: Apertura sin señal
- **WHEN** el chofer ya cargó la app antes y la abre sin conexión
- **THEN** la app se muestra y comunica que no hay conexión, sin pantalla de error del navegador

### Requirement: Ruta activa en modo lectura sin conexión
El sistema SHALL conservar la última ruta activa consultada para mostrarla sin conexión, indicando que los datos pueden estar desactualizados.

#### Scenario: Ruta cargada y luego sin señal
- **WHEN** el chofer consultó su ruta activa y luego pierde la conexión
- **THEN** sigue viendo la lista de paradas y el mapa con las teselas ya cargadas, con un aviso de "sin conexión"

#### Scenario: Sin datos guardados
- **WHEN** el chofer abre la app sin conexión y nunca consultó una ruta en ese dispositivo
- **THEN** la app informa que necesita conexión para ver su ruta

### Requirement: Acciones que escriben requieren conexión
El sistema SHALL deshabilitar las acciones que modifican la ruta (llegada, entrega, fallo, salto, iniciar) cuando no hay conexión, explicando el motivo.

#### Scenario: Entregar sin señal
- **WHEN** el chofer sin conexión intenta marcar una parada como entregada
- **THEN** la acción no se envía y se muestra un mensaje de que necesita conexión

#### Scenario: Recupera conexión
- **WHEN** el dispositivo recupera la conexión
- **THEN** el aviso desaparece, la ruta se refresca desde el servidor y las acciones se habilitan

### Requirement: Sin datos de sesión en almacenamiento persistente
El sistema SHALL NOT guardar credenciales ni el token de sesión en almacenamiento del navegador accesible desde JavaScript; la ruta cacheada SHALL eliminarse al cerrar sesión.

#### Scenario: Cierre de sesión
- **WHEN** el chofer cierra sesión
- **THEN** la ruta cacheada localmente se elimina
