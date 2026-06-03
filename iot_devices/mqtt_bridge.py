# iot_devices/mqtt_bridge.py
import time
import json
import threading
import requests
import paho.mqtt.client as mqtt

# CONFIGURACIÓN DEL ENTORNO DE INGENIERÍA
BROKER = "broker.hivemq.com"
TOPIC_COMODIN = "fisi/smat/estaciones/#"  # Escucha multi-nodo gracias al comodín de multinivel '#'
API_URL = "http://localhost:8000/lecturas/"

# Coloca aquí un Token JWT válido generado por tu módulo de seguridad del backend
TOKEN_JWT = "TU_TOKEN_JWT_AUTENTICADO"  

# Diccionario global para el rastreo del tiempo de vida de los nodos (Keep-Alive)
last_seen = {}

def check_deadlines():
    """
    Hilo asíncrono de fondo (Resiliencia): Monitorea si los nodos LoRaWAN remotos
    pierden conectividad en zonas rurales sin cobertura 4G/Wi-Fi.
    """
    print("[MONITOR] Hilo asíncrono de Keep-Alive iniciado de forma persistente.")
    while True:
        current_time = time.time()
        # Evaluamos el estado de los nodos registrados
        for estacion_id, ultimo_timestamp in list(last_seen.items()):
            # Si el nodo no reporta datos en un umbral de 30 segundos (Gracia industrial)
            if current_time - ultimo_timestamp > 30:
                print(f"\n🚨 [ALERTA DE RESILIENCIA] ¡Estación {estacion_id} está OFFLINE!")
                print(f"   [ACCION] Notificando falla de enlace LoRaWAN al Backend...")
                
                # Opcional: Aquí disparas el estado a tu API de control
                # url_status = f"http://localhost:8000/estaciones/{estacion_id}/offline/"
                # requests.patch(url_status, headers={"Authorization": f"Bearer {TOKEN_JWT}"})
                
                # Eliminamos del rastreo activo para evitar spam de alertas en consola
                del last_seen[estacion_id]
                
        time.sleep(5)  # Ventana de evaluación periódica

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        print("\n✅ [BRIDGE] Conexión establecida con el Broker MQTT de forma exitosa.")
        client.subscribe(TOPIC_COMODIN)
        print(f"📡 [BRIDGE] Escuchando canales compartidos en: {TOPIC_COMODIN}")
    else:
        print(f"❌ [CRÍTICO] Error de enlace de red MQTT. Código: {rc}")

def on_message(client, userdata, msg):
    try:
        # 1. Decodificar el flujo binario crudo proveniente de la red
        raw_payload = msg.payload.decode()
        payload = json.loads(raw_payload)
        print(f"\n📩 [MQTT INGRESO] Mensaje detectado en {msg.topic}: {payload}")

        # 2. Extracción dinámica del Identificador de la Estación (Última sección del Tópico)
        estacion_id = msg.topic.split('/')[-1]

        # 3. Actualizar marcador de vida (Keep-Alive) del nodo para evitar alerta Offline
        last_seen[estacion_id] = time.time()

        # 4. Construcción del DTO estructurado exigido por el Backend
        data_to_send = {
            "valor": float(payload["valor"]),
            "estacion_id": int(estacion_id)
        }

        # 5. Puente de Red: Traducción asíncrona MQTT a petición síncrona HTTP POST con JWT
        headers = {"Authorization": f"Bearer {TOKEN_JWT}"}
        
        # Intentamos persistir el dato hacia el ecosistema de FastAPI
        try:
            response = requests.post(API_URL, json=data_to_send, headers=headers, timeout=5)
            if response.status_code == 200 or response.status_code == 201:
                print(f"   💾 [HTTP REST] Sincronización exitosa. Dato guardado en SQLite para nodo {estacion_id}.")
            else:
                print(f"   ⚠️ [API ERROR] Rechazo de servidor ({response.status_code}): {response.text}")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ [HTTP ERROR] Imposible conectar con FastAPI en {API_URL}. ¿El servidor está apagado?")

    except Exception as e:
        print(f"   ❌ [PROCESO ERROR] Imposible decodificar o enrutar el paquete: {e}")

def main():
    # Inicialización del demonio de monitoreo de vida en un hilo paralelo
    monitor_thread = threading.Thread(target=check_deadlines, daemon=True)
    monitor_thread.start()

    # Configuración del cliente con la API v2 moderna de Paho
    cliente = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    cliente.on_connect = on_connect
    cliente.on_message = on_message

    print("🚀 [SISTEMA] Inicializando MQTT-HTTP Gateway Bridge...")
    cliente.connect(BROKER, 1883, 60)
    
    # Mantener el hilo principal escuchando la red por siempre
    cliente.loop_forever()

if __name__ == "__main__":
    main()