import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from db.modelos import EstadoIncidencia, ResolucionIncidencia, TipoIncidencia


class IncidenciaCrear(BaseModel):
    tipo: TipoIncidencia
    descripcion: str | None = Field(None, max_length=500)
    # None = incidencia general de la ruta (ej. falla del vehículo).
    parada_id: uuid.UUID | None = None


class ResolverIncidencia(BaseModel):
    resolucion: ResolucionIncidencia


class IncidenciaPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tipo: TipoIncidencia
    descripcion: str | None
    fecha_hora: datetime
    ruta_id: uuid.UUID
    ruta_fecha: date
    parada_id: uuid.UUID | None
    # Del snapshot de la parada, para que siga mostrándose aunque el cliente
    # se borre de la libreta.
    parada_nombre: str | None
    estado: EstadoIncidencia
    resolucion: ResolucionIncidencia | None
    fecha_resolucion: datetime | None
    # Solo la de una parada fallida que todavía no se reprogramó: la UI no
    # ofrece "reprogramar" si esto es False.
    puede_reprogramarse: bool
