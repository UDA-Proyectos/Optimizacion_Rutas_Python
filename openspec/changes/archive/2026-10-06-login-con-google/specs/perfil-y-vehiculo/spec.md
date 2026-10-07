## MODIFIED Requirements

### Requirement: Cambiar contraseña
El sistema SHALL permitir cambiar la contraseña exigiendo la contraseña actual y confirmando la nueva, aplicando las mismas reglas de complejidad que el registro. Una cuenta sin contraseña (creada con Google) MUST NOT poder usar este flujo.

#### Scenario: Cambio correcto
- **WHEN** el chofer envía la contraseña actual correcta y una nueva válida confirmada
- **THEN** el sistema actualiza el hash y el chofer puede iniciar sesión solo con la nueva

#### Scenario: Contraseña actual incorrecta
- **WHEN** el chofer envía una contraseña actual incorrecta
- **THEN** el sistema responde 400 y no cambia la contraseña

#### Scenario: Confirmación distinta
- **WHEN** la nueva contraseña y su confirmación no coinciden
- **THEN** el sistema responde 422

#### Scenario: Cuenta sin contraseña
- **WHEN** un usuario cuya cuenta no tiene contraseña intenta cambiarla
- **THEN** el sistema responde 400 indicando que la cuenta entra con Google, y no le asigna ninguna contraseña
