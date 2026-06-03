# Sistema de Telemetría Industrial Híbrido (MQTT / LoRaWAN & HTTP REST)

## 1. Descripción del Proyecto
Este proyecto implementa una arquitectura de software desacoplada de nivel industrial para el monitoreo de telemetría en tiempo real, diseñada originalmente para el control de la cadena de frío en cámaras frigoríficas (Callao) y estaciones de monitoreo ambiental rural (SMAT). 

La solución resuelve las limitaciones físicas y de red de la web tradicional mediante un **MQTT-HTTP Gateway Bridge (Puente)**, permitiendo que nodos de bajo consumo (LoRaWAN/MQTT) transmitan ráfagas de datos ligeras de forma asíncrona, mientras que el Backend (FastAPI) centraliza la persistencia en SQLite y sirve los datos mediante endpoints HTTP REST estables y protegidos con seguridad JWT.

---

## 2. Arquitectura de la Solución y Flujo de Datos
El ecosistema está completamente desacoplado y estructurado en tres capas independientes:

1. **Capa de Transmisión (Nodos IoT):** El script `mqtt_sender.py` simula estaciones remotas enviando payloads JSON ligeros hacia un Broker MQTT público (`broker.hivemq.com`).
2. **Capa de Integración (The Gateway Bridge):** El script `mqtt_bridge.py` actúa como suscriptor del tópico comodín multinivel `fisi/smat/estaciones/#`. Procesa los mensajes, inyecta el token de seguridad y los redirige síncronamente vía HTTP POST al backend.
3. **Capa de Persistencia y API (Backend):** Una infraestructura construida en **FastAPI** y **SQLAlchemy** que valida los datos con **Pydantic v2**, los almacena en una base de datos relacional SQLite (`smat_industrial.db`) y expone endpoints de consulta.

---

## 3. Lógica de Resiliencia y Tolerancia a Fallos
* **Validación de Límites Físicos:** El backend utiliza esquemas de Pydantic para interceptar de forma inmediata cualquier payload corrupto o inyección de valores fuera de los límites lógicos (125°C o cadenas de texto inválidas).
* **Captura de Excepciones No Bloqueante:** Si el Bridge o el Suscriptor detectan un paquete corrupto, este se descarta para proteger la integridad de la base de datos, registrando el incidente detalladamente en un archivo local `log_errores.txt` sin tumbar el servicio.
* **Monitoreo Keep-Alive asíncrono (Detección Offline):** Mediante el uso de hilos paralelos (`threading.Thread`), el Bridge rastrea el último mensaje recibido de cada estación. Si un nodo rural LoRaWAN interrumpe sus transmisiones por más de 30 segundos, el sistema dispara automáticamente una alerta de **Estación Offline** en la consola de supervisión.

---

## 4. Cuestionario de Evaluación (Metodología de Tobón)

### 4.1 Pregunta Crítica: Viabilidad de HTTP REST frente a MQTT en Ingesta Masiva
**Pregunta:** ¿Por qué no es viable utilizar una arquitectura síncrona HTTP REST para interconectar 10,000 sensores industriales que reportan datos cada segundo? Justifique su respuesta basándose en hilos de ejecución de servidor y sobrecarga de paquetes.

**Respuesta:**
No es viable debido al colapso por concurrencia en el servidor y al desperdicio crítico de ancho de banda:

* **Hilos de Ejecución del Servidor:** HTTP es un protocolo síncrono basado en el modelo solicitud-respuesta sobre conexiones TCP que nacen y mueren continuamente. Si 10,000 sensores transmiten cada segundo de manera síncrona, el servidor web tendría que mantener, encolar o conmutar miles de hilos de ejecución (*threads*) en paralelo. Esto destruye la memoria del servidor por sobrecarga de cambio de contexto (*context switching*) y agota rápidamente el *pool* de sockets disponibles, provocando denegación de servicio (Timeout).
* **Sobrecarga de Paquetes (Overhead):** Una solicitud HTTP REST requiere el envío de cabeceras en texto plano (User-Agent, Content-Type, cookies, etc.) que superan fácilmente los **500 bytes** por cada paquete, incluso si el dato útil (*payload*) es solo un número de temperatura de 4 bytes. MQTT, en contraste, utiliza una cabecera fija estructurada de apenas **2 bytes**. A gran escala, HTTP consumiría megabytes por segundo únicamente en metadatos innecesarios, saturando los canales de comunicación de la planta industrial.

### 4.2 Pregunta Práctica: Escenarios Imperativos para QoS 2
**Pregunta:** Explique en qué escenarios de desarrollo de software es imperativo utilizar el nivel QoS 2 en lugar de QoS 0.

**Respuesta:**
El nivel **QoS 2 (Exactly Once / Exactamente una vez)** es imperativo en escenarios críticos donde la pérdida de un mensaje es inaceptable, pero la duplicidad del mismo provocaría un fallo catastrófico en la lógica del negocio o del proceso físico. Ejemplos de aplicación:

1. **Sistemas de Dosificación Automatizada:** En una planta de manufactura química o farmacéutica, enviar la orden de "inyectar 10 ml de reactivo" con QoS 1 podría duplicar la dosis si el paquete de confirmación se pierde en la red. QoS 2 asegura, mediante su saludo de cuatro vías, que la acción se ejecute estrictamente una sola vez.
2. **Telemetría Financiera o Facturación por Consumo:** Sistemas industriales donde el cobro de servicios de energía o agua depende directamente de los pulsos métricos enviados por el hardware a la base de datos. Un mensaje duplicado alteraría de forma errónea o ilegal el cobro real al usuario.

### 4.3 Reflexión Ética / Responsabilidad Social Universitaria (RSU)
**Pregunta:** El uso ineficiente de protocolos de red aumenta el procesamiento en centros de datos, incrementando la huella de carbono. ¿Cómo contribuye el diseño de protocolos eficientes como MQTT a la sostenibilidad tecnológica de las regiones rurales del Perú?

**Respuesta:**
Lejos de ser solo un aspecto técnico, el diseño de arquitecturas ligeras como MQTT y LoRaWAN representa una alternativa de sostenibilidad real directamente aplicable a la geografía y realidad rural peruana:

* **Reducción del Impacto Ambiental:** Al optimizar las cabeceras a solo 2 bytes, se reduce drásticamente el volumen de datos que los servidores en la nube deben procesar y almacenar. Esto reduce directamente el consumo eléctrico de refrigeración y cómputo en los centros de datos, mitigando la huella de carbono global asociada al software.
* **Inclusión Económica y Tecnológica:** Las zonas rurales del Perú (comunidades agrícolas aisladas, cuencas de ríos altoandinos) carecen de infraestructuras de telecomunicaciones de alta velocidad o redes de energía estables. Protocolos eficientes permiten que dispositivos IoT operen durante años alimentados por pequeñas baterías o paneles solares mínimos, transmitiendo bajo enlaces de radio de largo alcance y bajo costo (LoRaWAN). Esto hace técnica y económicamente viable el monitoreo de recursos vitales (como alertas de desbordes o heladas) en comunidades vulnerables, promoviendo una ingeniería con alta responsabilidad social y ecológica.