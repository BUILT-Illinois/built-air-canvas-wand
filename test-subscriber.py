import json
import time
from awscrt import mqtt
from awsiot import mqtt_connection_builder

IOT_ENDPOINT = "aevqdnds5bghe-ats.iot.us-east-1.amazonaws.com"  # Your endpoint
CERT_PATH = "certs/device-certificate.pem.crt"
KEY_PATH = "certs/device-private.pem.key"
CA_PATH = "certs/AmazonRootCA1.pem"
CLIENT_ID = "Test-Subscriber"
MQTT_TOPIC = "imu/raspberrypi_01/data"

message_count = 0

def on_message_received(topic, payload, **kwargs):
    global message_count
    message_count += 1
    
    try:
        message = json.loads(payload)
        data = message.get('data', {})
        accel = data.get('accelerometer', {})
        
        print(f"[{message_count}] Received! Accel: ({accel.get('x', 0):.2f}, {accel.get('y', 0):.2f}, {accel.get('z', 0):.2f})")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("Connecting to AWS IoT Core...")
    
    connection = mqtt_connection_builder.mtls_from_path(
        endpoint=IOT_ENDPOINT,
        cert_filepath=CERT_PATH,
        pri_key_filepath=KEY_PATH,
        ca_filepath=CA_PATH,
        client_id=CLIENT_ID,
        clean_session=False,
        keep_alive_secs=30
    )
    
    connect_future = connection.connect()
    connect_future.result()
    print("✓ Connected")
    
    subscribe_future, packet_id = connection.subscribe(
        topic=MQTT_TOPIC,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received
    )
    subscribe_future.result()
    print("✓ Subscribed to", MQTT_TOPIC)
    print("\nListening for messages... (Ctrl+C to stop)\n")
    
    try:
        # Just sleep and let callbacks work
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        connection.disconnect()

if __name__ == "__main__":
    main()