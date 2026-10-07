import uuid

from pydantic import BaseModel, EmailStr

from api.schemas_auth import VehiculoPublico


class ChoferDeEmpresa(BaseModel):
    id: uuid.UUID
    nombre_completo: str
    email: EmailStr
    telefono: str | None
    activo: bool
    vehiculo: VehiculoPublico | None
    rutas_del_dia: int
    tiene_ruta_en_curso: bool
