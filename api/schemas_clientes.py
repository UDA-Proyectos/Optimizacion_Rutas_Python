import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.validaciones import validar_ventana


class ClienteCrear(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=200)
    direccion: str = Field(..., min_length=3, max_length=300)
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    telefono: str | None = Field(default=None, max_length=30)
    # Valores habituales que se precargan al armar una ruta; cada ruta puede
    # cambiarlos puntualmente sin tocar el lugar.
    demanda_carga_default: int | None = Field(default=None, ge=0)
    tiempo_servicio_default: int = Field(default=0, ge=0, le=240)
    ventana_inicio_default: int | None = Field(default=None, ge=0, le=1440)
    ventana_fin_default: int | None = Field(default=None, ge=0, le=1440)

    @model_validator(mode="after")
    def _ventana_valida(self):
        validar_ventana(self.ventana_inicio_default, self.ventana_fin_default)
        return self


class ClienteActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=200)
    direccion: str | None = Field(default=None, min_length=3, max_length=300)
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)
    telefono: str | None = None
    demanda_carga_default: int | None = Field(default=None, ge=0)
    tiempo_servicio_default: int | None = Field(default=None, ge=0, le=240)
    ventana_inicio_default: int | None = Field(default=None, ge=0, le=1440)
    ventana_fin_default: int | None = Field(default=None, ge=0, le=1440)

    @model_validator(mode="after")
    def _campos_habituales_validos(self):
        enviados = self.model_fields_set
        # La columna no admite NULL: "sin tiempo de servicio" es 0, no null.
        if "tiempo_servicio_default" in enviados and self.tiempo_servicio_default is None:
            raise ValueError("El tiempo de servicio no puede ser nulo (usá 0).")
        if enviados & {"ventana_inicio_default", "ventana_fin_default"}:
            validar_ventana(self.ventana_inicio_default, self.ventana_fin_default)
        return self


class ClientePublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    direccion: str
    latitud: float
    longitud: float
    telefono: str | None
    demanda_carga_default: int | None
    tiempo_servicio_default: int
    ventana_inicio_default: int | None
    ventana_fin_default: int | None
    activo: bool
    fecha_creacion: datetime
