from flask import Flask, request, jsonify, send_from_directory
from azure.storage.blob import BlobServiceClient
import json
from datetime import datetime
import base64
import os

app = Flask(__name__)

# Azure configuration
connection_string = "DefaultEndpointsProtocol=https;AccountName=storagepocfp;AccountKey=knMauwPkBOLyM3VGxQE7RS8j7KJFOLyHahtQOApA0JMRT1JNUH5heBtV+C61oalS3x3MFCAnk/tT+ASt8s+oiw==;EndpointSuffix=core.windows.net"
container_name = "mycontainerfp"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

@app.route('/all_data')
def get_all_data():
    date_str = request.args.get("timestamp")
    print(f"[INFO] Timestamp recibido: {date_str}")

    if not date_str:
        print("[WARN] No se proporcionó timestamp")
        return jsonify({})

    try:
        year, month, day = date_str.split("-")
    except ValueError:
        print("[ERROR] Timestamp mal formateado")
        return jsonify({})

    prefix = "IoTHubFP/"
    blobs = list(container_client.list_blobs(name_starts_with=prefix))
    print(f"[INFO] Total de blobs encontrados con prefix '{prefix}': {len(blobs)}")

    horses_data = {}

    for blob in blobs:
        print(f"[DEBUG] Revisando blob: {blob.name}")

        if f"/{year}/{month}/{day}/" not in blob.name:
            print(f"[SKIP] Blob fuera de la fecha: {blob.name}")
            continue

        print(f"[MATCH] Blob válido para la fecha: {blob.name}")
        blob_client = container_client.get_blob_client(blob.name)

        try:
            blob_data = blob_client.download_blob().readall().decode("utf-8")
        except Exception as e:
            print(f"[ERROR] No se pudo leer blob {blob.name}: {e}")
            continue

        for line in blob_data.strip().splitlines():
            print(f"[DEBUG] Línea en blob: {line[:100]}...")

            try:
                record = json.loads(line)
            except Exception as e:
                print(f"[ERROR] JSON inválido en línea: {e}")
                continue

            system_props = record.get("SystemProperties", {})
            timestamp = system_props.get("enqueuedTime")
            device_id = system_props.get("connectionDeviceId", "").lower()
            print(f"[INFO] Dispositivo: {device_id}, Timestamp: {timestamp}")

            body_raw = record.get("Body")
            if not body_raw:
                print("[WARN] No hay campo 'Body'")
                continue

            if "horse" in device_id:
                if isinstance(body_raw, str):
                    try:
                        body_json = json.loads(body_raw)
                    except json.JSONDecodeError as e:
                        print(f"[ERROR] No se pudo decodificar string JSON: {e}")
                        continue
                else:
                    body_json = body_raw

                horse_id = device_id.replace("edgedevicehorse", "").strip()
                print(f"[INFO] horse_id: {horse_id}")
                body_json["horse_id"] = horse_id
                body_json["timestamp"] = timestamp

                if horse_id not in horses_data:
                    horses_data[horse_id] = []
                horses_data[horse_id].append(body_json)
                print(f"[OK] Añadido dato para horse_id {horse_id}")

            elif "stable" in device_id:
                print("[INFO] Dispositivo de establo, ignorado")
                continue

            else:
                print(f"[INFO] Dispositivo desconocido: {device_id}")
                continue

    print(f"[FINAL] Total de caballos encontrados: {len(horses_data)}")
    return jsonify(horses_data)



@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
