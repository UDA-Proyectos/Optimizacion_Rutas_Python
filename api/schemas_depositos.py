import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.validaciones import validar_ventana


class DepositoCrear(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=200)
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    ventana_inicio: int | None = Field(default=None, ge=0, le=1440)
    ventana_fin: int | None = Field(default=None, ge=0, le=1440)

    @model_validator(mode="after")
    def _ventana_valida(self):
        validar_ventana(self.ventana_inicio, self.ventana_fin)
        return self


class DepositoActualizar(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=200)
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)
    ventana_inicio: int | None = Field(default=None, ge=0, le=1440)
    ventana_fin: int | None = Field(default=None, ge=0, le=1440)

    @model_validator(mode="after")
    def _ventana_valida(self):
        if self.model_fields_set & {"ventana_inicio", "ventana_fin"}:
            validar_ventana(self.ventana_inicio, self.ventana_fin)
        return self


class DepositoPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nombre: str
    latitud: float
    longitud: float
    ventana_inicio: int | None
    ventana_fin: int | None
    activo: bool
    fecha_creacion: datetime
