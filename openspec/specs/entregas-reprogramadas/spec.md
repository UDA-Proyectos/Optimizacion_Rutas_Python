# entregas-reprogramadas Specification

## Purpose
Permite no perder una entrega que no se pudo hacer: queda reprogramada para su dueño (el chofer independiente o la empresa) y el sistema la ofrece ya cargada al armar la próxima ruta.

## Requirements

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
El sistema SHALL listar las entregas reprogramadas todavía sin cumplir de su dueño, y SHALL omitir las de lugares dados de baja y las de otros dueños. El dueño es el chofer independiente o, en una empresa, la empresa: el admin ve todas las de su empresa, sin importar qué chofer falló la entrega.

#### Scenario: Listado propio
- **WHEN** el chofer independiente consulta sus entregas pendientes
- **THEN** recibe solo las suyas, con lugar, dirección, carga, bultos, ventana y fecha de origen

#### Scenario: Lugar dado de baja
- **WHEN** el lugar de una entrega reprogramada fue dado de baja de la libreta
- **THEN** esa entrega no aparece en el listado

#### Scenario: Entregas de la empresa
- **WHEN** el admin consulta las entregas pendientes
- **THEN** recibe las reprogramadas de toda su empresa, incluidas las que fallaron distintos choferes

#### Scenario: Chofer de empresa
- **WHEN** un chofer de empresa consulta las entregas pendientes
- **THEN** el sistema responde 403

### Requirement: Precarga al armar la ruta
El sistema SHALL precargar las entregas pendientes del dueño, ya seleccionadas y con sus datos, al armar una ruta nueva, y SHALL permitir desmarcarlas o modificar sus valores para esa ruta. En una empresa, las precarga al admin al armar una ruta para cualquiera de sus choferes.

#### Scenario: Ruta nueva con reprogramadas
- **WHEN** el chofer empieza a armar una ruta y tiene entregas pendientes
- **THEN** esos lugares aparecen marcados con su carga y se identifican como reprogramados

#### Scenario: Desmarcar
- **WHEN** el chofer desmarca una entrega reprogramada y confirma la ruta
- **THEN** la entrega sigue pendiente para una ruta posterior

#### Scenario: Admin asigna una reprogramada a otro chofer
- **WHEN** el admin arma una ruta para un chofer distinto del que falló la entrega y la deja marcada
- **THEN** la entrega queda incluida en la ruta de ese otro chofer

### Requirement: Cierre al incluirla en una ruta
El sistema SHALL dar por incluida una entrega pendiente cuando el chofer confirma o edita una ruta que contiene ese lugar, y SHALL dejar de mostrarla como pendiente.

#### Scenario: Ruta confirmada con la entrega
- **WHEN** el chofer confirma una ruta que incluye el lugar de una entrega pendiente
- **THEN** la entrega deja de estar pendiente y no se vuelve a ofrecer

#### Scenario: Ruta cancelada o editada sin el lugar
- **WHEN** el chofer cancela la ruta que había incluido una entrega pendiente, o la edita y ya no contiene ese lugar
- **THEN** la entrega vuelve a estar pendiente y se vuelve a ofrecer en la próxima ruta
