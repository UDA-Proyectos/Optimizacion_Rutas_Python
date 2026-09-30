from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class VentanaHoraria(BaseModel):
    inicio: int = Field(..., description="Minuto de inicio de la ventana")
    fin: int = Field(..., description="Minuto de fin de la ventana")

    @model_validator(mode="after")
    def _fin_despues_del_inicio(self):
        if self.fin <= self.inicio:
            raise ValueError("La ventana horaria debe terminar después de empezar.")
        return self


class Coordenada(BaseModel):
    latitud: float
    longitud: float


class Cliente(BaseModel):
    id_cliente: str
    ubicacion: Coordenada
    demanda_carga: int = Field(..., ge=0)
    tiempo_servicio: int = Field(default=0)
    ventana_horaria: Optional[VentanaHoraria] = None


class Deposito(BaseModel):
    ubicacion: Coordenada
    ventana_horaria: Optional[VentanaHoraria] = None


class Vehiculo(BaseModel):
    id_vehiculo: str
    capacidad: int = Field(..., gt=0)


class PeticionRutas(BaseModel):
    tipo_problema: Literal["CVRP", "VRPTW"]
    deposito: Deposito
    clientes: List[Cliente]
    vehiculos: List[Vehiculo]
