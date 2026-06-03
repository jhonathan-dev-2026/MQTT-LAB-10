# backend/app/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ==========================================
# ESQUEMAS PARA LAS CÁMARAS FRIGORÍFICAS
# ==========================================
class CamaraBase(BaseModel):
    codigo_camara: str = Field(..., max_length=50, examples=["CAMARA-01"])
    descripcion: Optional[str] = Field(None, max_length=200, examples=["Cámara de congelado rápido - Lomo de Atún"])

class CamaraCreate(CamaraBase):
    pass

class Camara(CamaraBase):
    id: int

    class ConfigDict:
        from_attributes = True


# ==========================================
# ESQUEMAS PARA LA TELEMETRÍA MQTT
# ==========================================
class LecturaMQTTCreate(BaseModel):
    sensor_id: str = Field(..., examples=["CAMARA-01"])  # Mapeará con el ID dinámico del tópico
    timestamp: float = Field(..., description="Epoch timestamp generado por el sensor")
    valor: float = Field(..., ge=-50.0, le=100.0, description="Validación estricta de límites físicos", examples=[2.4])
    unidad: str = Field(default="Celsius", max_length=20)

class LecturaMQTTResponse(BaseModel):
    id: int
    camara_id: int
    timestamp_sensor: float
    valor_temperatura: float
    unidad: str
    fecha_registro: datetime

    class ConfigDict:
        from_attributes = True