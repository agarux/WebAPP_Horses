from flask import Flask, jsonify, send_from_directory, request
from azure.storage.blob import BlobServiceClient
import json
import base64
from datetime import datetime, timedelta

app = Flask(__name__)

connection_string = "DefaultEndpointsProtocol=https;AccountName=storagehorses;AccountKey=h4eBr4ZWS4UZuzvBiQKgcgNYsNFTAtR6IxLRKi2bldCfgen3pxrYUJ4zL6AyYTzvSINoCsPJ6dTq+ASt8QpPSw==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("horse-container")

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/list_blobs')
def list_blobs():
    ts = request.args.get("timestamp")  # Ej: 2025-05-09
    if not ts:
        return jsonify({"error": "Falta timestamp"}), 400

    try:
        dt = datetime.strptime(ts, "%Y-%m-%d")
        prefix = f"{dt.year:04d}/{dt.month:02d}/{dt.day:02d}"
    except:
        return jsonify({"error": "Formato de fecha inválido"}), 400

    partitions = ["caballo", "establo"]
    full_prefixes = [f"iot-hub-horses/{p}/{prefix}" for p in partitions]

    blobs = []
    for p in full_prefixes:
        blobs += list(container_client.list_blobs(name_starts_with=p))

    return jsonify([b.name for b in blobs])


@app.route('/all_data')
def all_data():
    all_messages = []

    ts = request.args.get("timestamp")  # format: 2025-05-09
    if not ts:
        return jsonify({"error": "Missing timestamp"}), 400

    try:
        dt = datetime.strptime(ts, "%Y-%m-%d")
        date_prefix = f"{dt.year}/{dt.month:02d}/{dt.day:02d}/"
    except Exception as e:
        return jsonify({"error": "Invalid timestamp format"}), 400

    print(f"Buscando blobs para la fecha: {date_prefix}")

    blobs = list(container_client.list_blobs(name_starts_with="iot-hub-horses/"))
    for blob in blobs:
        if not blob.name.endswith(".json"):
            continue

        # Asegúrate de que contiene la fecha solicitada
        if date_prefix not in blob.name:
            continue

        print(f"Procesando blob: {blob.name}")
        blob_client = container_client.get_blob_client(blob.name)
        try:
            blob_bytes = blob_client.download_blob().readall()
            lines = blob_bytes.splitlines()

            for line in lines:
                try:
                    outer_json = json.loads(line)
                    body_b64 = outer_json.get("Body")
                    if not body_b64:
                        continue

                    decoded_str = base64.b64decode(body_b64).decode("utf-8")
                    body_json = json.loads(decoded_str)

                    all_messages.append({
                        "timestamp": outer_json.get("EnqueuedTimeUtc", "N/A"),
                        **body_json
                    })

                except Exception as e:
                    print(f"Error decoding message: {e}")
                    continue

        except Exception as e:
            print(f"Error leyendo blob {blob.name}: {e}")
            continue

    return jsonify(all_messages)


@app.route('/get_horse_data/<int:horse_id>', methods=['GET'])
def get_horse_data(horse_id):
    blobs = list(container_client.list_blobs(name_starts_with="iot-hub-horses/"))
    blobs = sorted(blobs, key=lambda b: b.name, reverse=True)

    print(f"Total blobs encontrados: {len(blobs)}")

    for blob in blobs:
        if not blob.name.endswith(".json"):
            continue

        print(f"Procesando blob: {blob.name}")
        blob_client = container_client.get_blob_client(blob.name)

        try:
            blob_bytes = blob_client.download_blob().readall()
            lines = blob_bytes.splitlines()

            for line in lines:
                try:
                    outer_json = json.loads(line)
                    body_b64 = outer_json.get("Body")
                    if not body_b64:
                        continue

                    decoded_str = base64.b64decode(body_b64).decode("utf-8")
                    body_json = json.loads(decoded_str)

                    print(f"Mensaje decodificado: {body_json}")

                    if body_json.get("horse_id") != horse_id:
                        print(f"Ignorando: horse_id={body_json.get('horse_id')} no coincide con solicitado={horse_id}")
                        continue

                    return jsonify({
                        "bpm": body_json.get("bpm", 0),
                        "temperature": round(body_json.get("temperature", 0), 1),
                        "oxymetry": round(body_json.get("oxymetry", 0), 1),
                        "status": body_json.get("status", "Unknown"),
                        "location": body_json.get("location", "Unknown")
                    })

                except Exception as e:
                    print(f"Error procesando línea JSON: {e}")
                    continue

        except Exception as e:
            print(f"Error leyendo blob {blob.name}: {e}")
            continue

    return jsonify({"error": f"No data found for horse {horse_id}"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
