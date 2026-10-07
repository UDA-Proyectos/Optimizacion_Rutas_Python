# gestion-de-choferes Specification

## Purpose
Permite al admin de una empresa conocer a los choferes de su flota y sumar choferes nuevos con códigos de invitación generados desde la app, sin depender de llamadas manuales a la API.

## Requirements

### Requirement: Listar choferes de la empresa
El sistema SHALL listar al admin los choferes de su empresa con nombre, email, teléfono, vehículo (tipo, patente y capacidad) y un resumen de su día: cantidad de rutas de hoy y si tiene una ruta en curso. MUST NOT incluir choferes de otras empresas ni choferes independientes.

#### Scenario: Flota con choferes
- **WHEN** el admin consulta sus choferes
- **THEN** recibe a todos los choferes de su empresa con sus datos, su vehículo y el resumen de hoy

#### Scenario: Aislamiento entre empresas
- **WHEN** el admin consulta sus choferes y existen choferes de otra empresa
- **THEN** esos choferes no aparecen

#### Scenario: Rol no admin
- **WHEN** un chofer (de empresa o independiente) pide el listado de choferes
- **THEN** el sistema responde 403

### Requirement: Invitaciones desde la app
El sistema SHALL permitir al admin generar un código de invitación y ver los códigos de su empresa con su estado (usado o disponible), y SHALL permitirle copiar un código disponible para compartirlo.

#### Scenario: Generar y copiar
- **WHEN** el admin genera un código desde la sección Choferes
- **THEN** el código nuevo aparece disponible en el listado y se puede copiar con un toque

#### Scenario: Código ya usado
- **WHEN** un chofer se registró con un código
- **THEN** el listado lo muestra como usado y no ofrece copiarlo

#### Scenario: Chofer recién registrado
- **WHEN** un chofer se registra con un código de la empresa
- **THEN** aparece en el listado de choferes del admin
