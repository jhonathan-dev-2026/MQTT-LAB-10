# iot_devices/mqtt_sender.py
import paho.mqtt.client as mqtt
import json
import time
import random

# Configuración del Broker Público solicitado en la guía
BROKER = "broker.hivemq.com"
PORT = 1883

def main():
    # Inicializar cliente MQTT utilizando la API moderna v2 exigida por Paho
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    print(f"[SENSOR] Conectando al Broker de contingencia rural: {BROKER}...")
    client.connect(BROKER, PORT, 60)
    
    estaciones = [1, 2]
    iteracion = 0
    
    print("\n[SENSOR] Transmisor SMAT-LoRaWAN activo. Enviando telemetría de campo...")
    
    try:
        while True:
            iteracion += 1
            # Seleccionar estación de manera intercalada
            estacion_id = estaciones[iteracion % len(estaciones)]
            topic_dinamico = f"fisi/smat/estaciones/{estacion_id}"
            
            # SIMULACIÓN DE OPERACIÓN DE CAMPO: Telemetría ambiental
            payload = {
                "valor": round(random.uniform(20.0, 60.0), 2),
                "timestamp": time.time()
            }
            
            mensaje_json = json.dumps(payload)
            client.publish(topic_dinamico, mensaje_json, qos=1)
            print(f"[SENSOR] Transmitido vía MQTT a [{topic_dinamico}] -> {mensaje_json}")
            
            # Intervalo de simulación de envío de datos
            time.sleep(8)
            
    except KeyboardInterrupt:
        print("\n[SENSOR] Apagando transmisor de telemetría de contingencia...")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()