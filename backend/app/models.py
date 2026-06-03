# backend/app/models.py
from datetime import datetime
from sqlalchemy import ForeignKey, String, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class CamaraDB(Base):
    __tablename__ = "camaras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    codigo_camara: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    descripcion: Mapped[str] = mapped_column(String(200), nullable=True)

    # Relación inversa para acceder a las lecturas desde la cámara
    lecturas = relationship("LecturaMQTTDB", back_populates="camara", cascade="all, delete-orphan")


class LecturaMQTTDB(Base):
    __tablename__ = "lecturas_mqtt"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    camara_id: Mapped[int] = mapped_column(ForeignKey("camaras.id", ondelete="CASCADE"), nullable=False)
    
    # Datos de telemetría requeridos por el modelo industrial
    timestamp_sensor: Mapped[float] = mapped_column(Float, nullable=False)
    valor_temperatura: Mapped[float] = mapped_column(Float, nullable=False)
    unidad: Mapped[str] = mapped_column(String(20), default="Celsius")
    
    # Timestamp de inserción en el sistema (servidor)
    fecha_registro: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relación ORM hacia la entidad Cámara
    camara = relationship("CamaraDB", back_populates="lecturas")
