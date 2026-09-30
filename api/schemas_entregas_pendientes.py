import uuid
from datetime import date, datetime

from pydantic import BaseModel


class EntregaPendientePublica(BaseModel):
    """Una entrega reprogramada que se ofrece ya cargada al armar la próxima ruta.
    El lugar viene con nombre y dirección para poder mostrarla sin otro pedido."""

    id: uuid.UUID
    cliente_id: uuid.UUID
    cliente_nombre: str
    cliente_direccion: str
    carga_kg: int
    unidades: int
    ventana_inicio: int | None
    ventana_fin: int | None
    fecha_creacion: datetime
    # Día de la ruta en que no se pudo entregar.
    fecha_origen: date
