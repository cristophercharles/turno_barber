from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# =========================
# CLIENTES
# =========================
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)

    turnos = relationship(
        "Turno",
        back_populates="cliente",
        cascade="all, delete-orphan"
    )


# =========================
# JORNADA DEL DÍA
# =========================
class Jornada(Base):
    __tablename__ = "jornadas"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String, nullable=False)        # YYYY-MM-DD
    hora_inicio = Column(String, nullable=False)  # HH:MM
    hora_fin = Column(String, nullable=False)     # HH:MM

    activa = Column(Boolean, default=True)
    creada = Column(DateTime, default=datetime.utcnow)

    barberos = relationship(
        "Barbero",
        back_populates="jornada",
        cascade="all, delete-orphan"
    )


# =========================
# BARBEROS / SILLAS
# =========================
class Barbero(Base):
    __tablename__ = "barberos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    silla = Column(String, nullable=False)
    duracion = Column(Integer, nullable=False)  # minutos por turno

    jornada_id = Column(Integer, ForeignKey("jornadas.id"), nullable=False)

    jornada = relationship("Jornada", back_populates="barberos")
    turnos = relationship(
        "Turno",
        back_populates="barbero",
        cascade="all, delete-orphan"
    )


# =========================
# TURNOS
# =========================
class Turno(Base):
    __tablename__ = "turnos"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, nullable=False)
    fecha = Column(String, nullable=False)

    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    barbero_id = Column(Integer, ForeignKey("barberos.id"), nullable=False)
    jornada_id = Column(Integer, ForeignKey("jornadas.id"), nullable=False)

    hora = Column(String, nullable=False)
    estado = Column(String, default="esperando")

    inicio_real = Column(DateTime, nullable=True)
    fin_real = Column(DateTime, nullable=True)
    creado = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="turnos")
    barbero = relationship("Barbero", back_populates="turnos")
    jornada = relationship("Jornada")


# =========================
# BARBERÍAS
# =========================
class Barberia(Base):
    __tablename__ = "barberias"

    id = Column(String, primary_key=True, index=True)   # ABR-001
    nombre = Column(String, nullable=False)
    licencia_key = Column(String, unique=True, nullable=False)

    pantallas_tv = Column(Integer, default=1)
    activa = Column(Boolean, default=True)
    fecha_activacion = Column(DateTime, default=datetime.utcnow)

    licencias = relationship(
        "Licencia",
        back_populates="barberia",
        cascade="all, delete-orphan"
    )


# =========================
# LICENCIAS (TV / BARBERO / CLIENTE)
# =========================
class Licencia(Base):
    __tablename__ = "licencias"

    id = Column(Integer, primary_key=True, index=True)

    barberia_id = Column(
        String,
        ForeignKey("barberias.id"),
        nullable=False
    )

    app_tipo = Column(String, nullable=False)   # TV | BARBERO | CLIENTE
    max_uso = Column(Integer, default=1)
    uso_actual = Column(Integer, default=0)

    activa = Column(Boolean, default=True)
    creada = Column(DateTime, default=datetime.utcnow)

    barberia = relationship("Barberia", back_populates="licencias")
