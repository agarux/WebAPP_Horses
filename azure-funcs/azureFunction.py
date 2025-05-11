from azure.storage.blob import BlobServiceClient
import azure.functions as func
import logging
import json
from datetime import datetime

app = func.FunctionApp()

@app.function_name(name="HorseAlert")
@app.event_hub_message_trigger(
    arg_name="event",
    event_hub_name="horsedata",  
    connection="EventHubConnectionAppSetting"
)
def main(event: func.EventHubEvent):
    message = event.get_body().decode('utf-8')
    data = json.loads(message)

    heart_rate = data.get("hr")
    spo2 = data.get("spo2")
    temperature = data.get("temperature")

    log_entries = [
        f"Heart Rate: {heart_rate}",
        f"SpO2: {spo2}",
        f"Temperature: {temperature}"
    ]

    alerts = []

    if heart_rate and heart_rate > 100:
        alerts.append("⚠️ High heart rate")
    if spo2 and spo2 < 95:
        alerts.append("⚠️ Low SpO2 level")
    if temperature and temperature > 39:
        alerts.append("⚠️ High temperature")

    log_entries.append(f"ALERTS: {alerts}" if alerts else "✅ All good.")

    # Print logs to terminal for debugging
    for entry in log_entries:
        logging.info(entry)

    # Save logs to Blob Storage 
    log_text = "\n".join(log_entries)
    save_log_to_blob(log_text)

def save_log_to_blob(content: str):

    connection_string = "DefaultEndpointsProtocol=https;AccountName=horsefuncstorage;AccountKey=YOUR_KEY_HERE;EndpointSuffix=core.windows.net"
    
    container_name = "horselogs"
    blob_name = f"log-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.txt"

    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        
        # Create the container if it doesn't exist
        try:
            container_client.create_container()
        except Exception:
            pass  # Ignore if already exists

        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(content)
    except Exception as e:
        logging.error(f"Failed to save log to blob storage: {e}")
