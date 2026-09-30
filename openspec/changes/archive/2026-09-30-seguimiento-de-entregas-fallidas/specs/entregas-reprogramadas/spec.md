## Purpose

Permite al chofer independiente no perder una entrega que no pudo hacer: la deja reprogramada y el sistema se la ofrece ya cargada cuando arma su próxima ruta.

## ADDED Requirements

### Requirement: Reprogramar una entrega no realizada
El sistema SHALL permitir reprogramar una entrega cuya parada quedó fallida, guardándola para la próxima ruta con su lugar, su carga, sus bultos y su ventana horaria, y SHALL dejar registrado de qué parada proviene.

#### Scenario: Reprogramar una parada fallida
- **WHEN** el chofer reprograma la entrega de una parada fallida
- **THEN** queda guardada una entrega pendiente con el lugar, la carga y los bultos de esa parada

#### Scenario: Parada no fallida
- **WHEN** el chofer intenta reprogramar la entrega de una parada que no está fallida
- **THEN** el sistema responde 409 y no guarda nada

#### Scenario: Doble reprogramación
- **WHEN** se intenta reprogramar una entrega que ya fue reprogramada
- **THEN** el sistema responde 409 y no crea un duplicado

### Requirement: Listar entregas pendientes
El sistema SHALL listar las entregas reprogramadas todavía sin cumplir del chofer, y SHALL omitir las de lugares dados de baja y las de otros choferes.

#### Scenario: Listado propio
- **WHEN** el chofer consulta sus entregas pendientes
- **THEN** recibe solo las suyas, con lugar, dirección, carga, bultos, ventana y fecha de origen

#### Scenario: Lugar dado de baja
- **WHEN** el chofer eliminó de su libreta el lugar de una entrega reprogramada
- **THEN** esa entrega no aparece en el listado

### Requirement: Precarga al armar la ruta
El sistema SHALL precargar las entregas pendientes, ya seleccionadas y con sus datos, al armar una ruta nueva, y SHALL permitir al chofer desmarcarlas o modificar sus valores para esa ruta.

#### Scenario: Ruta nueva con reprogramadas
- **WHEN** el chofer empieza a armar una ruta y tiene entregas pendientes
- **THEN** esos lugares aparecen marcados con su carga y se identifican como reprogramados

#### Scenario: Desmarcar
- **WHEN** el chofer desmarca una entrega reprogramada y confirma la ruta
- **THEN** la entrega sigue pendiente para una ruta posterior

### Requirement: Cierre al incluirla en una ruta
El sistema SHALL dar por incluida una entrega pendiente cuando el chofer confirma o edita una ruta que contiene ese lugar, y SHALL dejar de mostrarla como pendiente.

#### Scenario: Ruta confirmada con la entrega
- **WHEN** el chofer confirma una ruta que incluye el lugar de una entrega pendiente
- **THEN** la entrega deja de estar pendiente y no se vuelve a ofrecer

#### Scenario: Ruta cancelada o editada sin el lugar
- **WHEN** el chofer cancela la ruta que había incluido una entrega pendiente, o la edita y ya no contiene ese lugar
- **THEN** la entrega vuelve a estar pendiente y se vuelve a ofrecer en la próxima ruta
