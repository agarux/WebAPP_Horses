from flask import Flask, request, jsonify, send_from_directory
from azure.storage.blob import BlobServiceClient
import base64
import json
from datetime import datetime
import os

app = Flask(__name__)

# Configuración de Azure
connection_string = "DefaultEndpointsProtocol=https;AccountName=storagepocfp;AccountKey=knMauwPkBOLyM3VGxQE7RS8j7KJFOLyHahtQOApA0JMRT1JNUH5heBtV+C61oalS3x3MFCAnk/tT+ASt8s+oiw==;EndpointSuffix=core.windows.net"
container_name = "mycontainerfp"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

@app.route('/all_data')
def get_all_data():
    date_str = request.args.get("timestamp")
    print(f"[INFO] Recibida fecha: {date_str}")
    if not date_str:
        print("[WARN] No se proporcionó timestamp.")
        return jsonify([])

    try:
        year, month, day = date_str.split("-")
    except ValueError:
        print("[ERROR] Formato de fecha incorrecto.")
        return jsonify([])

    prefix = f"IoTHubFP/00/{year}/{month}/{day}/"
    print(f"[INFO] Buscando blobs con prefijo: {prefix}")
    blobs = container_client.list_blobs(name_starts_with=prefix)

    all_data = []

    for blob in blobs:
        print(f"[INFO] Procesando blob: {blob.name}")
        blob_client = container_client.get_blob_client(blob.name)
        blob_data = blob_client.download_blob().readall().decode("utf-8")

        for line in blob_data.strip().splitlines():
            try:
                record = json.loads(line)
            except Exception as e:
                print(f"[ERROR] Línea no válida en {blob.name}: {e}")
                continue

            system_props = record.get("SystemProperties", {})
            timestamp = system_props.get("enqueuedTime")

            body_base64 = record.get("Body")
            if not body_base64:
                print("[WARN] Registro sin 'Body'")
                continue

            try:
                body_json = json.loads(base64.b64decode(body_base64).decode("utf-8"))
            except Exception as e:
                print(f"[ERROR] Fallo al decodificar body base64: {e}")
                continue

            device_id = system_props.get("connectionDeviceId", "").lower()
            print(f"[INFO] Dispositivo detectado: {device_id}")

            if "horse" in device_id:
                body_json["horse_id"] = device_id.replace("horse-", "").strip()
            elif "stable" in device_id:
                body_json["device"] = "stable"
            else:
                print(f"[WARN] Dispositivo desconocido: {device_id}")
                continue

            body_json["timestamp"] = timestamp
            all_data.append(body_json)

    print(f"[INFO] Registros totales procesados: {len(all_data)}")
    return jsonify(all_data)


# Ruta para archivos estáticos (favicon, logo, etc.)
@app.route('/static/<path:path>')
def send_static(path):
    print(f"[INFO] Solicitando archivo estático: {path}")
    return send_from_directory('static', path)

# Servir index.html
@app.route('/')
def index():
    print("[INFO] Solicitando index.html")
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    print("[INFO] Servidor Flask arrancando en http://0.0.0.0:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)
