import time
import random
import json
from azure.iot.device import IoTHubDeviceClient, Message

# Connection string of stable IoT device (temp, humd, pressure)
CONNECTION_STRING = "HostName=IoTHubFP.azure-devices.net;DeviceId=stable-device;SharedAccessKey=kPeFEZ5T5fKIFzorIZlI+mrWlaVr/vc+GyyWGQ8Ypqw="

# seconds to new mssg
telemetry_interval = 10

# IoT Hub
device_client = None

def set_telemetry_interval(method_name, payload, user_context):
    global telemetry_interval
    try:
        telemetry_interval = int(payload)
        print(f"New telemetry interval: {telemetry_interval} seconds")
        return 200, "{\"result\":\"Success\"}"
    except ValueError:
        print("Invalid value")
        return 400, "{\"result\":\"Invalid value\"}"

def send_device_to_cloud_messages():
    min_temp = 20
    max_temp = 33
    min_humidity = 30
    max_humidity = 60
    min_pressure = 980    # hPa (hectopascales)
    max_pressure = 1050
    random.seed()
    
    while True:
        temperature = random.uniform(min_temp, max_temp)
        humidity = random.uniform(min_humidity, max_humidity)
        pressure = random.uniform(min_pressure, max_pressure)

        message_data = {
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "pressure": round(pressure, 2)
        }

        message_string = json.dumps(message_data)
        message = Message(message_string)

        device_client.send_message(message)
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} > Mssg sent: {message_string}")

        time.sleep(telemetry_interval)

def main():
    global device_client
    device_client = IoTHubDeviceClient.create_from_connection_string(CONNECTION_STRING)
    device_client.on_method_request_received = set_telemetry_interval
    print("Stable simulator. Ctrl-C to EXIT.")
    send_device_to_cloud_messages()

if __name__ == "__main__":
    main()
