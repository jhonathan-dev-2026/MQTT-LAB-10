# iot_devices/publisher_reto.py
import time
import random
import json
import paho.mqtt.client as mqtt

# Configuración del Broker Público de Pruebas
BROKER = "broker.hivemq.com"
PUERTO = 1883

def conectar_mqtt():
    # Inicializar cliente MQTT utilizando la API moderna v2
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    print(f"[IOT] Conectando al broker industrial {BROKER}...")
    client.connect(BROKER, PUERTO, 60)
    return client

def main():
    cliente = conectar_mqtt()
    cliente.loop_start()  # Iniciar el bucle de red en un hilo de fondo
    
    # Identificadores de las cámaras frigoríficas (Sede Callao)
    camaras = ["CAMARA-01", "CAMARA-02"]
    iteracion = 0
    
    print("\n[IOT] Sistema de transmisión multitópico activo. Enviando telemetría...")
    
    try:
        while True:
            iteracion += 1
            # Alternar dinámicamente entre CAMARA-01 y CAMARA-02
            camara_actual = camaras[iteracion % len(camaras)]
            
            # Construcción jerárquica del tópico usando la estructura del reto
            topico_dinamico = f"unmsm/callao/camara/{camara_actual}/telemetria"
            
            # INYECCIÓN PLANIFICADA DE FALLAS (Cada 5 transmisiones)
            if iteracion % 5 == 0:
                print(f"\n[SISTEMA] >>> Generando anomalía intencional de datos <<<")
                
                fallas_posibles = [
                    # Falla 1: Tipo de dato incorrecto (String en lugar de Float)
                    {"timestamp": time.time(), "valor": "ERROR_TEMP", "unidad": "Celsius"},
                    # Falla 2: Fuera de los límites físicos definidos en Pydantic (ge=-50.0, le=100.0)
                    {"timestamp": time.time(), "valor": 125.0, "unidad": "Celsius"},
                    # Falla 3: Payload corrupto que rompe la estructura JSON
                    "MALFORMED_PACKET_TEXT_WITHOUT_JSON_STRUCTURE"
                ]
                
                datos_falla = random.choice(fallas_posibles)
                mensaje = json.dumps(datos_falla) if isinstance(datos_falla, dict) else datos_falla
                print(f"[IOT-ANOMALÍA] Transmitiendo paquete corrupto en: {topico_dinamico}")
            
            else:
                # OPERACIÓN NORMAL: Generar temperaturas frías de operación industrial
                # Ocasionalmente superará los 5.0 °C para activar las alertas de pérdida de frío
                temperatura = round(random.uniform(-15.0, 8.0), 2)
                
                datos_sensor = {
                    "timestamp": time.time(),
                    "valor": temperatura,
                    "unidad": "Celsius"
                }
                mensaje = json.dumps(datos_sensor)
            
            # Publicar el mensaje con QoS 1 para asegurar la entrega en la red
            info = cliente.publish(topico_dinamico, mensaje, qos=1)
            info.wait_for_publish()  # Bloqueo controlado para garantizar el handshake de red
            
            print(f"[IOT] Publicado con éxito en [{topico_dinamico}] -> {mensaje}")
            
            # Intervalo de simulación de 3 segundos
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n[IOT] Deteniendo el simulador de sensores industriales...")
    finally:
        cliente.loop_stop()
        cliente.disconnect()

if __name__ == "__main__":
    main()