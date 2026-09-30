## Purpose

Define cómo el chofer independiente avanza por las paradas de su ruta en curso: registra su llegada, entrega, informa que no pudo entregar o saltea una parada, hasta cerrar la ruta.

## ADDED Requirements

### Requirement: Registro de llegada a la parada
El sistema SHALL persistir la hora real de llegada cuando el chofer indica que llegó a la parada en curso, y SHALL conservarla al recargar la aplicación.

#### Scenario: Llegada registrada
- **WHEN** el chofer con una ruta en curso indica que llegó a la parada actual
- **THEN** el sistema guarda la hora real de llegada de esa parada y la devuelve en la ruta

#### Scenario: Llegada repetida
- **WHEN** el chofer indica llegada en una parada que ya tiene hora de llegada
- **THEN** el sistema conserva la hora original y no devuelve error

#### Scenario: Parada que no es la actual
- **WHEN** el chofer indica llegada en una parada que no está en curso
- **THEN** el sistema responde 409 y no modifica la parada

### Requirement: Entrega completada
El sistema SHALL marcar la parada como completada, registrar la hora real de salida y pasar la siguiente parada pendiente a en curso.

#### Scenario: Entrega sin llegada previa
- **WHEN** el chofer completa una parada en curso que no tiene hora de llegada
- **THEN** el sistema usa la hora de salida como hora de llegada y completa la parada

### Requirement: Entrega fallida con motivo
El sistema SHALL permitir marcar la parada en curso como fallida indicando un motivo obligatorio (cliente ausente, rechazo de entrega, dirección incorrecta, mercadería dañada u otro), SHALL registrar una incidencia asociada a esa parada y SHALL avanzar a la siguiente parada.

#### Scenario: Cliente ausente
- **WHEN** el chofer marca la parada en curso como fallida con motivo "cliente ausente"
- **THEN** la parada queda en estado fallida con ese motivo, se crea una incidencia asociada a la parada y la siguiente parada pasa a en curso

#### Scenario: Motivo faltante
- **WHEN** el chofer marca una parada como fallida sin motivo
- **THEN** el sistema responde 422 y no modifica la parada

### Requirement: Saltear una parada
El sistema SHALL permitir saltear la parada en curso, moviéndola al final del recorrido pendiente sin cancelarla, y SHALL pasar la siguiente parada a en curso.

#### Scenario: Salto con más paradas pendientes
- **WHEN** el chofer saltea la parada en curso y quedan otras paradas pendientes
- **THEN** la parada salteada queda pendiente después de las demás y la siguiente pasa a en curso

#### Scenario: Única parada restante
- **WHEN** el chofer intenta saltear la única parada que queda
- **THEN** el sistema responde 409 indicando que debe entregarla o marcarla como fallida

### Requirement: Cierre de la ruta
El sistema SHALL marcar la ruta como completada y registrar la hora real de fin cuando no quedan paradas pendientes ni en curso, aunque alguna haya terminado como fallida.

#### Scenario: Última parada fallida
- **WHEN** el chofer marca como fallida la última parada pendiente
- **THEN** la ruta pasa a completada con hora de fin real registrada
