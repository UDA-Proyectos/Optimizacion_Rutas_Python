import enum
import uuid
from datetime import date, datetime
from typing import NamedTuple

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class RolUsuario(str, enum.Enum):
    CHOFER = "chofer"
    ADMIN = "admin"


class PlanSuscripcion(str, enum.Enum):
    PRUEBA = "prueba"
    BASICO = "basico"
    PREMIUM = "premium"


class TipoVehiculo(str, enum.Enum):
    MOTO = "moto"
    AUTO = "auto"
    CAMIONETA = "camioneta"
    FURGON = "furgon"
    CAMION = "camion"


class TipoProblema(str, enum.Enum):
    CVRP = "CVRP"
    VRPTW = "VRPTW"


class EstadoRuta(str, enum.Enum):
    PLANIFICADA = "planificada"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


class EstadoParada(str, enum.Enum):
    PENDIENTE = "pendiente"
    EN_CURSO = "en_curso"
    COMPLETADA = "completada"
    FALLIDA = "fallida"


class TipoIncidencia(str, enum.Enum):
    CLIENTE_AUSENTE = "cliente_ausente"
    RECHAZO_ENTREGA = "rechazo_entrega"
    DIRECCION_INCORRECTA = "direccion_incorrecta"
    MERCADERIA_DANADA = "mercaderia_danada"
    PROBLEMA_VEHICULO = "problema_vehiculo"
    OTRO = "otro"


class EstadoIncidencia(str, enum.Enum):
    PENDIENTE = "pendiente"
    RESUELTA = "resuelta"


class ResolucionIncidencia(str, enum.Enum):
    REPROGRAMADA = "reprogramada"
    CERRADA = "cerrada"


class EstadoEntregaPendiente(str, enum.Enum):
    PENDIENTE = "pendiente"
    INCLUIDA = "incluida"


class SuscripcionMixin:
    """Campos de plan compartidos por Empresa y Usuario (chofer independiente paga su propio plan)."""

    plan: Mapped[PlanSuscripcion] = mapped_column(
        Enum(PlanSuscripcion, name="plan_suscripcion", native_enum=False),
        nullable=False,
        default=PlanSuscripcion.PRUEBA,
    )
    fecha_fin_prueba: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DuenioMixin:
    """FKs de dueño compartidas por los recursos que puede tener una empresa
    (flota) o un chofer independiente — mismo patrón que Usuario.empresa_id.
    Al menos una de las dos debe estar seteada (se valida en db/crud.py)."""

    empresa_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=True
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )


class Duenio(NamedTuple):
    """Identifica a quién pertenecen los recursos de DuenioMixin (Vehiculo de
    reserva, Deposito, Cliente): a una empresa (compartidos entre su flota) o
    a un chofer independiente — nunca ambos. Ver Usuario.ambito_dueño."""

    empresa_id: uuid.UUID | None
    usuario_id: uuid.UUID | None


class Empresa(SuscripcionMixin, Base):
    __tablename__ = "empresas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(
        back_populates="empresa", foreign_keys="Usuario.empresa_id"
    )
    codigos_invitacion: Mapped[list["CodigoInvitacion"]] = relationship(
        back_populates="empresa", foreign_keys="CodigoInvitacion.empresa_id"
    )
    vehiculos: Mapped[list["Vehiculo"]] = relationship(
        back_populates="empresa", foreign_keys="Vehiculo.empresa_id"
    )
    depositos: Mapped[list["Deposito"]] = relationship(
        back_populates="empresa", foreign_keys="Deposito.empresa_id"
    )
    clientes: Mapped[list["Cliente"]] = relationship(
        back_populates="empresa", foreign_keys="Cliente.empresa_id"
    )


class Usuario(SuscripcionMixin, Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(200), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        Enum(RolUsuario, name="rol_usuario", native_enum=False),
        nullable=False,
        default=RolUsuario.CHOFER,
    )

    empresa_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=True
    )

    # Teléfono de contacto — NULL para admins de empresa (no manejan) y para
    # cuentas creadas antes de que este campo existiera. Los datos del vehículo
    # viven en Vehiculo (usuario.vehiculos), no acá.
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)

    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    empresa: Mapped["Empresa | None"] = relationship(
        back_populates="usuarios", foreign_keys=[empresa_id]
    )
    vehiculos: Mapped[list["Vehiculo"]] = relationship(
        back_populates="usuario",
        foreign_keys="Vehiculo.usuario_id",
        order_by="Vehiculo.fecha_creacion.desc()",
    )
    depositos: Mapped[list["Deposito"]] = relationship(
        back_populates="usuario", foreign_keys="Deposito.usuario_id"
    )
    clientes: Mapped[list["Cliente"]] = relationship(
        back_populates="usuario", foreign_keys="Cliente.usuario_id"
    )
    rutas: Mapped[list["Ruta"]] = relationship(
        back_populates="chofer", foreign_keys="Ruta.chofer_id"
    )

    @property
    def vehiculo(self) -> "Vehiculo | None":
        """Vehículo actualmente asignado — el más reciente si por algún motivo
        hay más de uno (Vehiculo.usuario_id no lleva historial, solo el estado
        actual, y nada fuerza a un único vehículo activo a nivel de DB)."""
        return self.vehiculos[0] if self.vehiculos else None

    @property
    def ambito_dueño(self) -> Duenio:
        """A quién pertenecen los Vehiculo/Deposito/Cliente que este usuario
        puede crear o listar: los de su empresa si pertenece a una (los
        comparte con el resto de la flota), o los suyos propios si es
        independiente. Único lugar donde vive esta regla — routers y CRUD
        de cada recurso la consumen en vez de reimplementarla."""
        if self.empresa_id is not None:
            return Duenio(empresa_id=self.empresa_id, usuario_id=None)
        return Duenio(empresa_id=None, usuario_id=self.id)

    def __repr__(self) -> str:
        return f"<Usuario {self.email} rol={self.rol.value}>"


class CodigoInvitacion(Base):
    __tablename__ = "codigos_invitacion"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(12), unique=True, nullable=False, index=True)

    empresa_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("empresas.id"), nullable=False
    )
    creado_por_usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )
    usado_por_usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )

    usado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fecha_uso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    empresa: Mapped["Empresa"] = relationship(
        back_populates="codigos_invitacion", foreign_keys=[empresa_id]
    )
    creado_por: Mapped["Usuario"] = relationship(foreign_keys=[creado_por_usuario_id])
    usado_por: Mapped["Usuario | None"] = relationship(foreign_keys=[usado_por_usuario_id])


class Vehiculo(DuenioMixin, Base):
    __tablename__ = "vehiculos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tipo_vehiculo: Mapped[TipoVehiculo] = mapped_column(
        Enum(TipoVehiculo, name="tipo_vehiculo", native_enum=False), nullable=False
    )
    patente: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    capacidad_carga_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    # Chofer actualmente asignado (usuario_id, heredado de DuenioMixin). NULL =
    # vehículo de reserva sin asignar (solo posible con empresa_id seteado; un
    # independiente siempre tiene uno). Sin historial de reasignaciones.
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    empresa: Mapped["Empresa | None"] = relationship(
        back_populates="vehiculos", foreign_keys="Vehiculo.empresa_id"
    )
    usuario: Mapped["Usuario | None"] = relationship(
        back_populates="vehiculos", foreign_keys="Vehiculo.usuario_id"
    )
    rutas: Mapped[list["Ruta"]] = relationship(back_populates="vehiculo")


class Deposito(DuenioMixin, Base):
    __tablename__ = "depositos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    latitud: Mapped[float] = mapped_column(Float, nullable=False)
    longitud: Mapped[float] = mapped_column(Float, nullable=False)
    ventana_inicio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ventana_fin: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    empresa: Mapped["Empresa | None"] = relationship(
        back_populates="depositos", foreign_keys="Deposito.empresa_id"
    )
    usuario: Mapped["Usuario | None"] = relationship(
        back_populates="depositos", foreign_keys="Deposito.usuario_id"
    )
    rutas: Mapped[list["Ruta"]] = relationship(back_populates="deposito")


class Cliente(DuenioMixin, Base):
    __tablename__ = "clientes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    direccion: Mapped[str] = mapped_column(String(300), nullable=False)
    latitud: Mapped[float] = mapped_column(Float, nullable=False)
    longitud: Mapped[float] = mapped_column(Float, nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Defaults reutilizados al armar una ruta nueva — cada ParadaRuta puede
    # pisarlos puntualmente (ver snapshot en ParadaRuta) sin tocar el Cliente.
    demanda_carga_default: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tiempo_servicio_default: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ventana_inicio_default: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ventana_fin_default: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    empresa: Mapped["Empresa | None"] = relationship(
        back_populates="clientes", foreign_keys="Cliente.empresa_id"
    )
    usuario: Mapped["Usuario | None"] = relationship(
        back_populates="clientes", foreign_keys="Cliente.usuario_id"
    )


class Ruta(Base):
    __tablename__ = "rutas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    chofer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )
    vehiculo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehiculos.id"), nullable=False
    )
    deposito_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("depositos.id"), nullable=False
    )
    # Quién confirmó/asignó la ruta (un admin de empresa, o el propio chofer
    # si es independiente) — distinto de chofer_id cuando es una empresa.
    creado_por_usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )

    fecha: Mapped[date] = mapped_column(Date, nullable=False)
    # Para distinguir varias rutas del mismo día ("Mañana", "Zona norte").
    nombre: Mapped[str | None] = mapped_column(String(60), nullable=True)
    tipo_problema: Mapped[TipoProblema] = mapped_column(
        Enum(TipoProblema, name="tipo_problema", native_enum=False), nullable=False
    )
    estado: Mapped[EstadoRuta] = mapped_column(
        Enum(EstadoRuta, name="estado_ruta", native_enum=False),
        nullable=False,
        default=EstadoRuta.PLANIFICADA,
    )
    # Totales que devuelve el solver al confirmar — distancia en metros
    # (matriz OSRM), tiempo en minutos, igual que routing/solver.py.
    distancia_total_m: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tiempo_total_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Mismo texto que ya se mostraba en el preview (routing/planificador.py) —
    # se persiste para que siga visible en "Ruta de hoy" después de confirmar,
    # no solo durante el preview efímero previo a confirmar.
    explicacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    hora_inicio_real: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    hora_fin_real: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Minuto del día en que el solver VRPTW estimó la vuelta al depósito —
    # None en modo CVRP, que no calcula tiempos (ver routing/solver.py).
    hora_fin_estimada_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    chofer: Mapped["Usuario"] = relationship(back_populates="rutas", foreign_keys=[chofer_id])
    vehiculo: Mapped["Vehiculo"] = relationship(back_populates="rutas", foreign_keys=[vehiculo_id])
    deposito: Mapped["Deposito"] = relationship(back_populates="rutas", foreign_keys=[deposito_id])
    creado_por: Mapped["Usuario"] = relationship(foreign_keys=[creado_por_usuario_id])
    paradas: Mapped[list["ParadaRuta"]] = relationship(
        back_populates="ruta", order_by="ParadaRuta.orden"
    )
    incidencias: Mapped[list["Incidencia"]] = relationship(back_populates="ruta")

    @property
    def capacidad_vehiculo_kg(self) -> int:
        return self.vehiculo.capacidad_carga_kg

    @property
    def incidencias_total(self) -> int:
        return len(self.incidencias)


class ParadaRuta(Base):
    __tablename__ = "paradas_ruta"
    __table_args__ = (UniqueConstraint("ruta_id", "orden"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    ruta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rutas.id"), nullable=False
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False
    )
    orden: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[EstadoParada] = mapped_column(
        Enum(EstadoParada, name="estado_parada", native_enum=False),
        nullable=False,
        default=EstadoParada.PENDIENTE,
    )

    # Snapshot del Cliente al momento de confirmar la ruta — si el Cliente
    # cambia de dirección/ventana después, esta parada ya asignada no se mueve.
    nombre_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    direccion_snapshot: Mapped[str] = mapped_column(String(300), nullable=False)
    latitud_snapshot: Mapped[float] = mapped_column(Float, nullable=False)
    longitud_snapshot: Mapped[float] = mapped_column(Float, nullable=False)
    demanda_carga_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    unidades_snapshot: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    distancia_acumulada_m: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tiempo_servicio_snapshot: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ventana_inicio_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ventana_fin_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)

    hora_estimada_llegada: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hora_real_llegada: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    hora_real_salida: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Saltear no deja un estado propio (la parada vuelve a pendiente al final
    # del recorrido); este contador es lo único que lo registra, para el
    # resumen de cierre.
    veces_salteada: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    # Copia del motivo de la Incidencia que se crea al fallar la parada: el
    # historial y la timeline lo leen sin join. NULL salvo en paradas fallidas.
    motivo_fallo: Mapped[TipoIncidencia | None] = mapped_column(
        Enum(TipoIncidencia, name="motivo_fallo", native_enum=False), nullable=True
    )

    ruta: Mapped["Ruta"] = relationship(back_populates="paradas", foreign_keys=[ruta_id])
    cliente: Mapped["Cliente"] = relationship(foreign_keys=[cliente_id])
    prueba_entrega: Mapped["PruebaEntrega | None"] = relationship(
        back_populates="parada", uselist=False
    )
    incidencias: Mapped[list["Incidencia"]] = relationship(back_populates="parada")


class PruebaEntrega(Base):
    __tablename__ = "pruebas_entrega"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    parada_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paradas_ruta.id"), unique=True, nullable=False
    )
    foto_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    firma_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    nombre_receptor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parada: Mapped["ParadaRuta"] = relationship(
        back_populates="prueba_entrega", foreign_keys=[parada_id]
    )


class Incidencia(Base):
    __tablename__ = "incidencias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    ruta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rutas.id"), nullable=False
    )
    # NULL = incidencia general de la ruta (ej. falla del vehículo), no atada
    # a una parada puntual.
    parada_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paradas_ruta.id"), nullable=True
    )
    tipo: Mapped[TipoIncidencia] = mapped_column(
        Enum(TipoIncidencia, name="tipo_incidencia", native_enum=False), nullable=False
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    reportado_por_usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )
    fecha_hora: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Seguimiento: nace pendiente y el chofer la resuelve (reprogramando la
    # entrega o cerrándola sin más acción).
    estado: Mapped[EstadoIncidencia] = mapped_column(
        Enum(EstadoIncidencia, name="estado_incidencia", native_enum=False),
        nullable=False,
        default=EstadoIncidencia.PENDIENTE,
    )
    resolucion: Mapped[ResolucionIncidencia | None] = mapped_column(
        Enum(ResolucionIncidencia, name="resolucion_incidencia", native_enum=False),
        nullable=True,
    )
    fecha_resolucion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    ruta: Mapped["Ruta"] = relationship(back_populates="incidencias", foreign_keys=[ruta_id])
    parada: Mapped["ParadaRuta | None"] = relationship(
        back_populates="incidencias", foreign_keys=[parada_id]
    )
    reportado_por: Mapped["Usuario"] = relationship(foreign_keys=[reportado_por_usuario_id])


class EntregaPendiente(Base):
    """Entrega no realizada que el chofer reprogramó para su próxima ruta.

    Es un compromiso a futuro con ciclo de vida propio (pendiente -> incluida),
    separado de la ParadaRuta de origen, que es el historial de ese día y no se
    modifica. Guarda un snapshot de lo que había que entregar."""

    __tablename__ = "entregas_pendientes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    usuario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False
    )
    cliente_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False
    )
    # Única: una parada fallida se reprograma una sola vez.
    parada_origen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("paradas_ruta.id"), unique=True, nullable=False
    )
    incidencia_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("incidencias.id"), nullable=True
    )

    carga_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    unidades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ventana_inicio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ventana_fin: Mapped[int | None] = mapped_column(Integer, nullable=True)

    estado: Mapped[EstadoEntregaPendiente] = mapped_column(
        Enum(EstadoEntregaPendiente, name="estado_entrega_pendiente", native_enum=False),
        nullable=False,
        default=EstadoEntregaPendiente.PENDIENTE,
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    fecha_inclusion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Ruta que la incluyó: si esa ruta se cancela, la entrega vuelve a pendiente.
    ruta_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rutas.id"), nullable=True
    )

    cliente: Mapped["Cliente"] = relationship(foreign_keys=[cliente_id])
    parada_origen: Mapped["ParadaRuta"] = relationship(foreign_keys=[parada_origen_id])
