import uuid
from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from db.modelos import EstadoParada, EstadoRuta, TipoIncidencia, TipoProblema

# Margen antes del cierre de una ventana horaria para marcar una parada
# "en riesgo" (todavía no vencida, pero al filo) — puramente de UI, no
# afecta al solver.
MARGEN_RIESGO_MIN = 15


def _minuto_del_dia(momento: datetime) -> int:
    local = momento.astimezone()
    return local.hour * 60 + local.minute


def _usa_ventanas_horarias(tipo_problema: TipoProblema) -> bool:
    return tipo_problema == TipoProblema.VRPTW


class ParadaSeleccionada(BaseModel):
    cliente_id: uuid.UUID
    carga_kg: int = Field(..., ge=0)
    # Bultos/unidades — informativo, no entra en la dimensión de capacidad
    # del solver (esa sigue siendo carga_kg). Default 0 para no romper
    # clientes de la API que todavía no lo mandan.
    unidades: int = Field(0, ge=0)
    ventana_inicio: int | None = Field(None, ge=0, le=1440)
    ventana_fin: int | None = Field(None, ge=0, le=1440)


class OptimizarRutaRequest(BaseModel):
    paradas: list[ParadaSeleccionada] = Field(..., min_length=1)
    usa_ventanas_horarias: bool = False
    # None = el primer depósito del chofer (comportamiento previo).
    deposito_id: uuid.UUID | None = None
    # Día (calendario del chofer) para el que se planifica; None = hoy.
    fecha: date | None = None
    # Para distinguir varias rutas del mismo día.
    nombre: str | None = Field(None, max_length=60)
    # Solo el admin: a qué chofer de su empresa se le asigna la ruta.
    chofer_id: uuid.UUID | None = None

    @field_validator("nombre")
    @classmethod
    def _nombre_sin_espacios(cls, nombre: str | None) -> str | None:
        nombre = nombre.strip() if nombre else None
        return nombre or None


class IniciarRutaRequest(BaseModel):
    # Día local del chofer: el servidor no sabe en qué huso está.
    fecha_hoy: date | None = None


class FallarParadaRequest(BaseModel):
    motivo: TipoIncidencia
    descripcion: str | None = Field(None, max_length=500)
    # Dejar la entrega reprogramada para la próxima ruta en el mismo paso.
    reprogramar: bool = False

    @field_validator("motivo")
    @classmethod
    def _motivo_de_parada(cls, motivo: TipoIncidencia) -> TipoIncidencia:
        # Un problema del vehículo no es un motivo por el que falle *una*
        # parada: se reporta como incidencia general de la ruta.
        if motivo == TipoIncidencia.PROBLEMA_VEHICULO:
            raise ValueError("Ese motivo no aplica a una parada puntual.")
        return motivo


class ParadaPreview(BaseModel):
    cliente_id: uuid.UUID
    nombre: str
    direccion: str
    orden: int
    carga_kg: int
    unidades: int
    distancia_acumulada_m: int
    ventana_inicio: int | None = None
    ventana_fin: int | None = None
    hora_estimada_llegada: int | None = None


class RutaPreview(BaseModel):
    paradas: list[ParadaPreview]
    distancia_total_m: int
    carga_total_kg: int
    distancia_sin_optimizar_m: int
    ahorro_m: int
    explicacion: str
    usa_ventanas_horarias: bool = False
    hora_fin_estimada_min: int | None = None


class GeometriaRuta(BaseModel):
    tramos: list[list[tuple[float, float]]]


class ParadaRutaPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cliente_id: uuid.UUID
    orden: int
    estado: EstadoParada
    nombre_snapshot: str
    direccion_snapshot: str
    latitud_snapshot: float
    longitud_snapshot: float
    demanda_carga_snapshot: int
    unidades_snapshot: int
    distancia_acumulada_m: int
    ventana_inicio_snapshot: int | None
    ventana_fin_snapshot: int | None
    hora_estimada_llegada: int | None
    hora_real_llegada: datetime | None
    hora_real_salida: datetime | None
    veces_salteada: int
    motivo_fallo: TipoIncidencia | None

    @computed_field
    @property
    def en_riesgo(self) -> bool:
        """Solo tiene sentido con ventana horaria y mientras la parada
        sigue sin completarse — el solver ya garantiza que, de haber
        solución, toda ventana se cumple *en el plan*; esto marca cuándo el
        reloj real se está acercando al límite planificado."""
        if self.ventana_fin_snapshot is None or self.estado not in (
            EstadoParada.PENDIENTE,
            EstadoParada.EN_CURSO,
        ):
            return False
        ahora_min = _minuto_del_dia(datetime.now(UTC))
        return ahora_min >= self.ventana_fin_snapshot - MARGEN_RIESGO_MIN

    @computed_field
    @property
    def ventana_cumplida(self) -> bool | None:
        """None: no aplica (sin ventana, o todavía no se completó). Si no,
        si la salida real quedó dentro de la ventana planificada."""
        if self.ventana_fin_snapshot is None or self.hora_real_salida is None:
            return None
        return _minuto_del_dia(self.hora_real_salida) <= self.ventana_fin_snapshot


class DepositoResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    latitud: float
    longitud: float


class ResumenRuta(BaseModel):
    """Cómo resultó realmente una ruta terminada. La distancia es la
    *planificada*: no se registra el recorrido real del vehículo, así que no se
    presenta como recorrida."""

    duracion_min: int | None
    paradas_completadas: int
    paradas_fallidas: int
    paradas_salteadas: int
    carga_entregada_kg: int
    incidencias: int
    distancia_planificada_m: int | None
    # Solo con ventanas horarias (None si la ruta no las usó o ninguna
    # parada completada tenía ventana).
    ventanas_cumplidas: int | None
    ventanas_evaluadas: int | None
    ventanas_cumplidas_pct: int | None


def calcular_resumen(
    *,
    hora_inicio_real: datetime | None,
    hora_fin_real: datetime | None,
    paradas: list,
    usa_ventanas_horarias: bool,
    distancia_total_m: int | None,
    incidencias: int,
) -> ResumenRuta:
    """Función pura sobre paradas ya cargadas (cualquier objeto con `estado`,
    `demanda_carga_snapshot`, `veces_salteada` y `ventana_cumplida`)."""
    completadas = [p for p in paradas if p.estado == EstadoParada.COMPLETADA]
    duracion = (
        round((hora_fin_real - hora_inicio_real).total_seconds() / 60)
        if hora_inicio_real and hora_fin_real
        else None
    )

    cumplidas = evaluadas = pct = None
    if usa_ventanas_horarias:
        evaluadas = sum(1 for p in completadas if p.ventana_cumplida is not None)
        if evaluadas:
            cumplidas = sum(1 for p in completadas if p.ventana_cumplida is True)
            pct = round(100 * cumplidas / evaluadas)
        else:
            evaluadas = None

    return ResumenRuta(
        duracion_min=duracion,
        paradas_completadas=len(completadas),
        paradas_fallidas=sum(1 for p in paradas if p.estado == EstadoParada.FALLIDA),
        paradas_salteadas=sum(1 for p in paradas if p.veces_salteada > 0),
        carga_entregada_kg=sum(p.demanda_carga_snapshot for p in completadas),
        incidencias=incidencias,
        distancia_planificada_m=distancia_total_m,
        ventanas_cumplidas=cumplidas,
        ventanas_evaluadas=evaluadas,
        ventanas_cumplidas_pct=pct,
    )


class RutaPublica(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    fecha: date
    nombre: str | None
    estado: EstadoRuta
    tipo_problema: TipoProblema
    chofer_id: uuid.UUID
    chofer_nombre: str
    distancia_total_m: int | None
    hora_inicio_real: datetime | None
    hora_fin_real: datetime | None
    hora_fin_estimada_min: int | None
    fecha_creacion: datetime
    deposito: DepositoResumen
    capacidad_vehiculo_kg: int
    explicacion: str | None
    incidencias_total: int
    paradas: list[ParadaRutaPublica]

    @computed_field
    @property
    def usa_ventanas_horarias(self) -> bool:
        return _usa_ventanas_horarias(self.tipo_problema)

    @computed_field
    @property
    def resumen(self) -> ResumenRuta | None:
        """Solo una ruta completada tiene resumen — una en curso todavía no
        tiene duración ni porcentaje de ventanas que mostrar."""
        if self.estado != EstadoRuta.COMPLETADA:
            return None
        return calcular_resumen(
            hora_inicio_real=self.hora_inicio_real,
            hora_fin_real=self.hora_fin_real,
            paradas=self.paradas,
            usa_ventanas_horarias=self.usa_ventanas_horarias,
            distancia_total_m=self.distancia_total_m,
            incidencias=self.incidencias_total,
        )


class RutaHistorialItem(BaseModel):
    """Resumen liviano para la vista de mes del almanaque — sin las
    paradas, que solo hacen falta al abrir el detalle de un día.
    `paradas_total`/`paradas_completadas` se derivan de `Ruta.paradas` en
    el router (no hay attribute plano en el modelo), así que este schema
    siempre se construye a mano, nunca con `model_validate` directo."""

    id: uuid.UUID
    fecha: date
    nombre: str | None
    estado: EstadoRuta
    tipo_problema: TipoProblema
    chofer_nombre: str
    distancia_total_m: int | None
    paradas_total: int
    paradas_completadas: int
    paradas_fallidas: int
    incidencias_total: int

    @computed_field
    @property
    def usa_ventanas_horarias(self) -> bool:
        return _usa_ventanas_horarias(self.tipo_problema)
