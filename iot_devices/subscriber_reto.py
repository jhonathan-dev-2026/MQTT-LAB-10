# iot_devices/subscriber_reto.py
import os
import sys
import json
from datetime import datetime
import paho.mqtt.client as mqtt
from pydantic import ValidationError

# Añadimos el directorio raíz al path para poder importar el backend de forma limpia
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal
from backend.app.models import CamaraDB, LecturaMQTTDB
from backend.app.schemas import LecturaMQTTCreate  # CORREGIDO: Importación alineada con schemas.py

# Configuración de Red
BROKER = "broker.hivemq.com"
PUERTO = 1883
TOPICO_COMODIN = "unmsm/callao/camara/+/telemetria"
LOG_FILE = "log_errores.txt"

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("\n[SISTEMA] Conectado exitosamente al Broker HiveMQ.")
        client.subscribe(TOPICO_COMODIN)
        print(f"[SISTEMA] Escuchando red industrial mediante: {TOPICO_COMODIN}")
    else:
        print(f"[CRÍTICO] Fallo de conexión MQTT. Código: {rc}")

def on_message(client, userdata, msg):
    raw_payload = msg.payload.decode()
    
    # 1. Extracción dinámica del ID de la cámara desde el Tópico (Posición 3)
    # Ejemplo: "unmsm/callao/camara/CAMARA-01/telemetria" -> "CAMARA-01"
    topic_parts = msg.topic.split('/')
    id_camara_topico = topic_parts[3] if len(topic_parts) > 3 else "DESCONOCIDA"

    print(f"\n" + "="*60)
    print(f"[INGRESO] Mensaje detectado en canal: {msg.topic}")
    
    try:
        # 2. Parsear el JSON crudo
        datos_json = json.loads(raw_payload)
        
        # Inyectamos el id extraído del tópico para que Pydantic lo valide contextualmente
        datos_json["sensor_id"] = id_camara_topico
        
        # 3. Validación Estricta con Pydantic
        lectura_validada = LecturaMQTTCreate(**datos_json)  # CORREGIDO: Uso del esquema correcto
        
        # 4. Lógica de Alerta de Negocio (Cadena de frío crítica > 5.0 °C)
        if lectura_validada.valor > 5.0:
            print(f"  [PELIGRO] ¡Pérdida de cadena de frío en {id_camara_topico}! " 
                  f"Registrado: {lectura_validada.valor} {lectura_validada.unidad}")
        else:
            print(f"  [OK] Parámetros térmicos estables en {id_camara_topico}: "
                  f"{lectura_validada.valor} {lectura_validada.unidad}")

        # 5. Persistencia Física Directa en Base de Datos
        db = SessionLocal()
        try:
            # Buscamos si la cámara existe en la base de datos
            camara = db.query(CamaraDB).filter(CamaraDB.codigo_camara == id_camara_topico).first()
            if not camara:
                # Si la cámara reporta y no existe, la creamos dinámicamente de forma robusta
                camara = CamaraDB(codigo_camara=id_camara_topico, descripcion="Creada automáticamente por flujo MQTT")
                db.add(camara)
                db.commit()
                db.refresh(camara)

            # Insertamos la lectura estructurada
            nueva_lectura = LecturaMQTTDB(
                camara_id=camara.id,
                timestamp_sensor=lectura_validada.timestamp,
                valor_temperatura=lectura_validada.valor,
                unidad=lectura_validada.unidad
            )
            db.add(nueva_lectura)
            db.commit()
            print(f"  [BD] Registro insertado correctamente en SQLite.")
        except Exception as db_err:
            print(f"  [ERROR BD] No se pudo escribir en SQLite: {db_err}")
            db.rollback()
        finally:
            db.close()

    except (json.JSONDecodeError, ValidationError) as err:
        # 6. Tolerancia a Fallos: Captura de anomalías en Log Local sin tumbar el script
        timestamp_error = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"  [ALERTA DE SEGURIDAD] Payload corrupto interceptado. Descartando datos.")
        
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"[{timestamp_error}] Error procesando paquete en {msg.topic}.\n")
            log.write(f"Payload recibido: {raw_payload}\n")
            log.write(f"Detalle del error:\n{str(err)}\n")
            log.write("-" * 80 + "\n")
        print(f"  [LOG] Incidente documentado en '{LOG_FILE}'.")

def main():
    cliente = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_connect = on_connect
    cliente.on_message = on_message

    print("[SISTEMA] Inicializando receptor asíncrono SMAT-Industrial...")
    cliente.connect(BROKER, PUERTO, 60)
    
    # Bucle infinito síncrono para mantener el hilo de escucha activo
    cliente.loop_forever()

if __name__ == "__main__":
    main()