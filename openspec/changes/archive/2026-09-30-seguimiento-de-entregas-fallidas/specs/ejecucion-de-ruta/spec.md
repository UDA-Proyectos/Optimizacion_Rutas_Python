## MODIFIED Requirements

### Requirement: Entrega fallida con motivo
El sistema SHALL permitir marcar la parada en curso como fallida indicando un motivo obligatorio (cliente ausente, rechazo de entrega, dirección incorrecta, mercadería dañada u otro), SHALL registrar una incidencia asociada a esa parada y SHALL avanzar a la siguiente parada. Opcionalmente, en el mismo paso, el chofer SHALL poder pedir que la entrega quede reprogramada para la próxima ruta.

#### Scenario: Cliente ausente
- **WHEN** el chofer marca la parada en curso como fallida con motivo "cliente ausente"
- **THEN** la parada queda en estado fallida con ese motivo, se crea una incidencia pendiente asociada a la parada y la siguiente parada pasa a en curso

#### Scenario: Motivo faltante
- **WHEN** el chofer marca una parada como fallida sin motivo
- **THEN** el sistema responde 422 y no modifica la parada

#### Scenario: Fallar y reprogramar en un paso
- **WHEN** el chofer marca la parada como fallida y pide reprogramarla
- **THEN** la parada queda fallida, la entrega queda reprogramada para la próxima ruta y la incidencia queda resuelta como reprogramada

#### Scenario: Fallar sin decidir todavía
- **WHEN** el chofer marca la parada como fallida sin pedir reprogramarla
- **THEN** la incidencia queda pendiente y la entrega se puede reprogramar más tarde desde las incidencias
