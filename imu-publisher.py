import time
import json
from awscrt import mqtt
from awsiot import mqtt_connection_builder
import os

# AWS IoT Settings
IOT_ENDPOINT = "aevqdnds5bghe-ats.iot.us-east-1.amazonaws.com"
CERT_PATH = "certs/device-certificate.pem.crt"
KEY_PATH = "certs/device-private.pem.key"
CA_PATH = "certs/AmazonRootCA1.pem"
CLIENT_ID = "RaspberryPi-IMU-01"
MQTT_TOPIC = "air-canvas/data"

#IMU Settings
PUBLISH_RATE_HZ = 2  # Publish rate in Hz
SAMPLE_RATE_HZ = 100  # IMU sample rate in Hz

try:
    from adafruit_bno08x import (
        BNO_REPORT_ACCELEROMETER,
        BNO_REPORT_GYROSCOPE,
        BNO_REPORT_MAGNETOMETER,
        BNO_REPORT_ROTATION_VECTOR,
    )
    from adafruit_bno08x.i2c import BNO08X_I2C
    import board
    import busio

    i2c = busio.I2C(board.SCL, board.SDA)
    sensor = BNO08X_I2C(i2c)
    
    sensor.enable_feature(BNO_REPORT_ACCELEROMETER)
    sensor.enable_feature(BNO_REPORT_GYROSCOPE)
    sensor.enable_feature(BNO_REPORT_MAGNETOMETER)
    sensor.enable_feature(BNO_REPORT_ROTATION_VECTOR)

    IMU_AVAILABLE = True
    print("BNO085 sensor initialized successfully")
    
except ImportError:
    print("WARNING: BNO085 library not found. Using mock data for testing.")
    print("Install with: pip3 install adafruit-circuitpython-bno08x --break-system-packages")
    IMU_AVAILABLE = False
except Exception as e:
    print(f"ERROR: Failed to initialize BNO085 sensor: {e}")
    print("Using mock data for testing.")
    IMU_AVAILABLE = False


def quaternion_to_euler(quat):
    """
    Convert quaternion to Euler angles (heading, roll, pitch)
    quat format from BNO085: (i, j, k, real) or (x, y, z, w)
    Returns: (heading, roll, pitch) in degrees
    """
    if not quat or any(q is None for q in quat):
        return (0, 0, 0)
    
    import math
    
    # BNO085 quaternion format: (i, j, k, real)
    x, y, z, w = quat[0], quat[1], quat[2], quat[3]
    
    # Roll (rotation around x-axis)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    
    # Pitch (rotation around y-axis)
    sinp = 2 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)  # Use 90 degrees if out of range
    else:
        pitch = math.asin(sinp)
    
    # Yaw/Heading (rotation around z-axis)
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)
    
    # Convert to degrees
    roll_deg = math.degrees(roll)
    pitch_deg = math.degrees(pitch)
    yaw_deg = math.degrees(yaw)
    
    # Normalize heading to 0-360
    heading = (yaw_deg + 360) % 360
    
    return (heading, roll_deg, pitch_deg)

def read_imu_data():
    if IMU_AVAILABLE:
        try:
            accel = sensor.acceleration  # m/s²
            gyro = sensor.gyro  # rad/s
            mag = sensor.magnetic  # µT
            quat = sensor.quaternion  # (i, j, k, real)
            heading, roll, pitch = quaternion_to_euler(quat)

            return {
                "accelerometer": {
                    "x": round(accel[0], 4) if accel and accel[0] is not None else 0,
                    "y": round(accel[1], 4) if accel and accel[1] is not None else 0,
                    "z": round(accel[2], 4) if accel and accel[2] is not None else 0
                },
                "gyroscope": {
                    "x": round(gyro[0] * 57.2958, 4) if gyro and gyro[0] is not None else 0,  # rad/s to deg/s
                    "y": round(gyro[1] * 57.2958, 4) if gyro and gyro[1] is not None else 0,
                    "z": round(gyro[2] * 57.2958, 4) if gyro and gyro[2] is not None else 0
                },
                "magnetometer": {
                    "x": round(mag[0], 4) if mag and mag[0] is not None else 0,
                    "y": round(mag[1], 4) if mag and mag[1] is not None else 0,
                    "z": round(mag[2], 4) if mag and mag[2] is not None else 0
                },
                "orientation": {
                    "heading": round(heading, 2),
                    "roll": round(roll, 2),
                    "pitch": round(pitch, 2)
                },
                "quaternion": {
                    "w": round(quat[3], 4) if quat and quat[3] is not None else 1,
                    "x": round(quat[0], 4) if quat and quat[0] is not None else 0,
                    "y": round(quat[1], 4) if quat and quat[1] is not None else 0,
                    "z": round(quat[2], 4) if quat and quat[2] is not None else 0
                },
                "calibration": {
                    "system": 3,  # BNO085 auto-calibrates
                    "gyroscope": 3,
                    "accelerometer": 3,
                    "magnetometer": 3
                },
            }
        except Exception as e:
            print(f"Error reading BNO085: {e}")
            return None
    else:
        import random
        return {
            "accelerometer": {
                "x": round(random.uniform(-2, 2), 4),
                "y": round(random.uniform(-2, 2), 4),
                "z": round(random.uniform(8, 12), 4)
            },
            "gyroscope": {
                "x": round(random.uniform(-10, 10), 4),
                "y": round(random.uniform(-10, 10), 4),
                "z": round(random.uniform(-10, 10), 4)
            },
            "magnetometer": {
                "x": round(random.uniform(-50, 50), 4),
                "y": round(random.uniform(-50, 50), 4),
                "z": round(random.uniform(-50, 50), 4)
            },
            "orientation": {
                "heading": round(random.uniform(0, 360),2),
                "roll": round(random.uniform(-180, 180), 2),
                "pitch": round(random.uniform(-90, 90), 2)
            },
            "quaternion": {
                "w": 1.0,
                "x": 0.0,
                "y": 0.0,
                "z": 0.0
            },
            "calibration": {
                "system": 3,
                "gyroscope": 3,
                "accelerometer": 3,
                "magnetometer": 3
            },
        }

def calculate_statistics(samples):
    if not samples:
        return None
    
    n = len(samples)

    #Calc means for accelerometer
    accel_x = sum(s['accelerometer']['x'] for s in samples) / n
    accel_y = sum(s['accelerometer']['y'] for s in samples) / n
    accel_z = sum(s['accelerometer']['z'] for s in samples) / n

    #Calc means for gyroscope
    gyro_x = sum(s['gyroscope']['x'] for s in samples) / n
    gyro_y = sum(s['gyroscope']['y'] for s in samples) / n
    gyro_z = sum(s['gyroscope']['z'] for s in samples) / n

    #Calc means for magnetometer
    mag_x = sum(s['magnetometer']['x'] for s in samples) / n
    mag_y = sum(s['magnetometer']['y'] for s in samples) / n
    mag_z = sum(s['magnetometer']['z'] for s in samples) / n

    latest = samples[-1]

    return {
        "accelerometer": {
            "x": round(accel_x, 4),
            "y": round(accel_y, 4),
            "z": round(accel_z, 4)
        },
        "gyroscope": {
            "x": round(gyro_x, 4),
            "y": round(gyro_y, 4),
            "z": round(gyro_z, 4)
        },
        "magnetometer": {
            "x": round(mag_x, 4),
            "y": round(mag_y, 4),
            "z": round(mag_z, 4)
        },
        "orientation": latest['orientation'],
        "quaternion": latest['quaternion'],
        "calibration": latest['calibration'],
    }

class IMUPublisher:
    def __init__(self, endpoint, cert_path, key_path, ca_path, client_id, topic):
        self.endpoint = endpoint
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path
        self.client_id = client_id
        self.topic = topic
        self.connection = None
        self.connected = False
    
    def connect(self):
        try:
            print(f"Connecting to AWS IoT Core: {self.endpoint}")
            
            self.connection = mqtt_connection_builder.mtls_from_path(
                endpoint=self.endpoint,
                cert_filepath=self.cert_path,
                pri_key_filepath=self.key_path,
                ca_filepath=self.ca_path,
                client_id=self.client_id,
                clean_session=False,
                keep_alive_secs=30
            )

            connect_future = self.connection.connect()
            connect_future.result()
            self.connected = True
            print("Connected to AWS IoT Core! :)")

        except Exception as e:
            print(f"Connection failed: {e} :(")
            self.connected = False
    
    def publish(self, data):
        if not self.connected or not self.connection:
            return False
        
        try:
            payload = {
                "timestamp": int(time.time() * 1000),
                "client_id": self.client_id,
                "data": data
            }

            message = json.dumps(payload)

            self.connection.publish(
                topic=self.topic,
                payload=message,
                qos=mqtt.QoS.AT_LEAST_ONCE
            )

            return True
        except Exception as e:
            print(f"Publish error: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        if self.connection:
            try:
                disconnect_future = self.connection.disconnect()
                disconnect_future.result()
                print("Disconnected from AWS IoT Core.")
            except Exception as e:
                print(f"Disconnection error: {e}")
        
        self.connected = False
    
def main():
    publisher = IMUPublisher(
        endpoint=IOT_ENDPOINT,
        cert_path=CERT_PATH,
        key_path=KEY_PATH,
        ca_path=CA_PATH,
        client_id=CLIENT_ID,
        topic=MQTT_TOPIC
    )

    publisher.connect()

    if not publisher.connected:
        print("Failed to connect to MQTT. Exiting.")
        return

    print(f"Publishing IMU data to topic: {MQTT_TOPIC}")
    print(f"Publish rate: {PUBLISH_RATE_HZ} Hz")
    print("Press Ctrl+C to stop\n")

    publish_interval = 1 / PUBLISH_RATE_HZ
    sample_interval = 1 / SAMPLE_RATE_HZ

    sample_buffer = []
    last_publish_time = time.time()
    message_count = 0

    try:
        while True:
            imu_data = read_imu_data()

            if imu_data:
                sample_buffer.append(imu_data)
            
            #Publish avg data at publish rate
            current_time = time.time()
            if current_time - last_publish_time >= publish_interval:
                if sample_buffer:
                    average_data = calculate_statistics(sample_buffer)

                    if publisher.publish(average_data):
                        message_count += 1
                        print(f"[{message_count}] Published: "
                            f"Accel ({average_data['accelerometer']['x']:.2f}, "
                            f"{average_data['accelerometer']['y']:.2f}, "
                            f"{average_data['accelerometer']['z']:.2f}) | "
                            f"Gyro ({average_data['gyroscope']['x']:.2f},  "
                            f"{average_data['gyroscope']['y']:.2f}, "
                            f"{average_data['gyroscope']['z']:.2f}) | "
                            f"Heading: {average_data['orientation']['heading']:.1f}° | ")
                        
                        sample_buffer = []
                        last_publish_time = current_time
            
            time.sleep(sample_interval)

    except KeyboardInterrupt:
        print("\n\nStopping IMU publisher...")
    finally:
        publisher.disconnect()
        print(f"Total messages published: {message_count}")

if __name__ == "__main__":
    main()