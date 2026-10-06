import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from db.modelos import PlanSuscripcion, RolUsuario, TipoVehiculo

# Reglas compartidas por el registro y por la edición de perfil/vehículo:
# una sola definición, para que no diverjan.
Contrasena = Annotated[str, Field(min_length=8, max_length=128)]
NombreCompleto = Annotated[str, Field(min_length=2, max_length=200)]
Telefono = Annotated[str, Field(min_length=6, max_length=30)]
Patente = Annotated[str, Field(min_length=4, max_length=12)]
CapacidadCargaKg = Annotated[int, Field(gt=0)]


class DatosPersona(BaseModel):
    email: EmailStr
    contrasena: Contrasena
    confirmar_contrasena: str
    nombre_completo: NombreCompleto

    @model_validator(mode="after")
    def validar_contrasenas_coinciden(self):
        if self.contrasena != self.confirmar_contrasena:
            raise ValueError("Las contraseñas no coinciden.")
        return self


class DatosVehiculo(BaseModel):
    telefono: Telefono
    tipo_vehiculo: TipoVehiculo
    patente: Patente
    capacidad_carga_kg: CapacidadCargaKg


def _rechazar_nulos(modelo: BaseModel, campos: tuple[str, ...]) -> None:
    """En un PATCH, "no enviado" y "enviado como null" son cosas distintas: las
    columnas de estos campos no admiten NULL, así que un null explícito es un
    error de validación y no un 500 al guardar."""
    for campo in campos:
        if campo in modelo.model_fields_set and getattr(modelo, campo) is None:
            raise ValueError(f"{campo} no puede ser nulo.")


class PerfilActualizar(BaseModel):
    """El email no se edita: si viene en el cuerpo, se ignora."""

    nombre_completo: NombreCompleto | None = None
    telefono: Telefono | None = None

    @model_validator(mode="after")
    def _sin_nulos(self):
        _rechazar_nulos(self, ("nombre_completo", "telefono"))
        return self


class VehiculoActualizar(BaseModel):
    tipo_vehiculo: TipoVehiculo | None = None
    patente: Patente | None = None
    capacidad_carga_kg: CapacidadCargaKg | None = None

    @model_validator(mode="after")
    def _normalizar(self):
        _rechazar_nulos(self, ("tipo_vehiculo", "patente", "capacidad_carga_kg"))
        if self.patente is not None:
            # El formulario de registro ya las manda en mayúsculas.
            self.patente = self.patente.upper()
        return self


class CambiarContrasena(BaseModel):
    contrasena_actual: str
    contrasena_nueva: Contrasena
    confirmar_contrasena_nueva: str

    @model_validator(mode="after")
    def validar_coinciden(self):
        if self.contrasena_nueva != self.confirmar_contrasena_nueva:
            raise ValueError("Las contraseñas no coinciden.")
        return self


class RegistroChoferIndependiente(DatosPersona, DatosVehiculo):
    pass


class RegistroEmpresa(DatosPersona):
    nombre_empresa: str = Field(..., min_length=2, max_length=200)


class RegistroChoferInvitado(DatosPersona, DatosVehiculo):
    codigo_invitacion: str = Field(..., min_length=8, max_length=12)


class CompletarRegistroGoogle(DatosVehiculo):
    nombre_completo: NombreCompleto


class DatosChoferGoogle(CompletarRegistroGoogle):
    """Lo que necesita crud.crear_chofer: el email sale del registro pendiente, no del body."""

    email: EmailStr


class RegistroGooglePendiente(BaseModel):
    email: EmailStr
    nombre_completo: str


class ProveedoresAuth(BaseModel):
    google: bool


class LoginRequest(BaseModel):
    email: EmailStr
    contrasena: str


class EmpresaPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    plan: PlanSuscripcion
    fecha_fin_prueba: datetime | None
    fecha_creacion: datetime


class VehiculoPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo_vehiculo: TipoVehiculo
    patente: str
    capacidad_carga_kg: int
    activo: bool


class UsuarioPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    nombre_completo: str
    rol: RolUsuario
    empresa_id: uuid.UUID | None
    telefono: str | None
    vehiculo: VehiculoPublico | None
    tiene_contrasena: bool
    plan: PlanSuscripcion
    fecha_fin_prueba: datetime | None
    fecha_creacion: datetime


class RegistroEmpresaResponse(BaseModel):
    usuario: UsuarioPublico
    empresa: EmpresaPublica


class CodigoInvitacionPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo: str
    usado: bool
    fecha_creacion: datetime
    fecha_uso: datetime | None


class MensajeResponse(BaseModel):
    mensaje: str
