import time
import random
import json
from azure.iot.device import IoTHubDeviceClient, Message

CONNECTION_STRING = "HostName=IoTHubFP.azure-devices.net;DeviceId=horses-test;SharedAccessKey=dENTqCnIEzl2Uio3ZBWrGmXyoxWdROaBudC/DqUMJ6k="

telemetry_interval = 10

# Cliente IoT Hub
device_client = None

def set_telemetry_interval(method_name, payload, user_context):
    """Manejo de método directo para establecer el intervalo de telemetría."""
    global telemetry_interval
    try:
        # Intentar analizar el valor de la carga útil
        telemetry_interval = int(payload)
        print(f"Nuevo intervalo de telemetría: {telemetry_interval} segundos")
        return 200, "{\"result\":\"Método directo ejecutado con éxito\"}"
    except ValueError:
        print("Valor inválido para el intervalo de telemetría")
        return 400, "{\"result\":\"Parámetro inválido\"}"

def send_device_to_cloud_messages():
    """Envía mensajes simulados al IoT Hub."""
    # Valores iniciales
    min_temp = 25
    min_oxymetry = 90
    min_bpm = 60
    random.seed()
    
    while True:
        # Generar valores aleatorios para la simulación
        horse_id = random.randint(1, 5)
        temperature = min_temp + random.uniform(0, 15)
        oxymetry = min_oxymetry + random.uniform(0, 5)
        bpm = min_bpm + random.randint(50, 100) 
        status = random.choice(["Standing", "Walking", "Trotting", "Running"])  
        # Crear el mensaje JSON
        message_data = {
            "horse_id": horse_id,
            "temperature": temperature,
            "oxymetry": oxymetry,
            "bpm": bpm,
            "status": status,
        }
        message_string = json.dumps(message_data)

        # Crear un mensaje para enviar
        message = Message(message_string)
        
        # Propiedad adicional: alerta de temperatura
        message.custom_properties["temperature_alert"] = "true" if temperature > 30 else "false"

        # Enviar el mensaje al IoT Hub
        device_client.send_message(message)
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} > Enviando mensaje: {message_string}")

        # Esperar el intervalo de telemetría
        time.sleep(telemetry_interval)

def main():
    """Conexión y ejecución principal."""
    global device_client

    # Crear cliente IoT Hub usando el protocolo MQTT
    device_client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    
    # Establecer el manejador del método directo para cambiar el intervalo de telemetría
    device_client.on_method_request_received = set_telemetry_interval

    # Iniciar el envío de mensajes
    print("Simulador de dispositivo IoT. Ctrl-C para salir.")
    send_device_to_cloud_messages()

if __name__ == "__main__":
    main()
