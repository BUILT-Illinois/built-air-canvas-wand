"""
eoh_imu_publisher.py — EOH Air Canvas IMU Publisher
Raspberry Pi Zero 2W + 2x Adafruit BNO085 on software I2C

Bus layout:
  Bus 8  — SDA: GPIO 16, SCL: GPIO 20  → IMU_TIP  (wand tip)
  Bus 10 — SDA: GPIO 05, SCL: GPIO 06  → IMU_BASE (wand base/grip)

Publishes rotation vector quaternions only to two MQTT topics:
  air-canvas/imu/tip
  air-canvas/imu/base

Each message:
  {
    "timestamp": <ms>,
    "client_id": "RaspberryPi-IMU-01",
    "data": {
      "quaternion": { "w": float, "x": float, "y": float, "z": float },
      "sample_count": int          # how many IMU reads were averaged
    }
  }
"""

import time
import json
from awscrt import mqtt
from awsiot import mqtt_connection_builder

# ─────────────────────────────────────────────
#  AWS IoT Settings
# ─────────────────────────────────────────────

IOT_ENDPOINT = "aevqdnds5bghe-ats.iot.us-east-1.amazonaws.com"
CERT_PATH    = "certs/device-certificate.pem.crt"
KEY_PATH     = "certs/device-private.pem.key"
CA_PATH      = "certs/AmazonRootCA1.pem"
CLIENT_ID    = "RaspberryPi-IMU-01"

TOPIC_WAND = "air-canvas/data/wand"

# ─────────────────────────────────────────────
#  IMU / Publish Settings
# ─────────────────────────────────────────────

PUBLISH_RATE_HZ = 30   # how often to publish averaged quaternion
SAMPLE_RATE_HZ  = 100  # how fast to poll the IMUs

# ─────────────────────────────────────────────
#  IMU Init — software I2C via ExtendedI2C
# ─────────────────────────────────────────────

try:
    from adafruit_extended_bus import ExtendedI2C as I2C
    from adafruit_bno08x.i2c import BNO08X_I2C
    from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR

    # Bus 8:  SDA=GPIO16, SCL=GPIO20 — wand tip
    i2c_tip  = I2C(8)
    imu_tip  = BNO08X_I2C(i2c_tip, address = 0x4A)
    imu_tip.enable_feature(BNO_REPORT_ROTATION_VECTOR)
    print("bus 8 (tip) initialized!")
    print("2 sec sleep!")
    time.sleep(2)
    # Bus 10: SDA=GPIO05, SCL=GPIO06 — wand base
    i2c_base = I2C(10)
    imu_base = BNO08X_I2C(i2c_base, address = 0x4A)
    print("2 sec sleep!")
    time.sleep(2)
    imu_base.enable_feature(BNO_REPORT_ROTATION_VECTOR)
    print("bus (base) initialized")

    IMU_AVAILABLE = True
    print("Both BNO085 sensors initialized successfully.")
    print("  Tip  → bus 8  (SDA=GPIO16, SCL=GPIO20)")
    print("  Base → bus 10 (SDA=GPIO05, SCL=GPIO06)")

except ImportError as e:
    print(f"WARNING: Missing library — {e}")
    print("Using mock quaternion data.")
    IMU_AVAILABLE = False
except Exception as e:
    print(f"ERROR: Failed to initialize IMUs — {e}")
    print("Using mock quaternion data.")
    IMU_AVAILABLE = False


# ─────────────────────────────────────────────
#  IMU Reading
# ─────────────────────────────────────────────

def read_quaternion(imu):
    """
    Read one rotation vector quaternion from a BNO085.
    bno.quaternion returns (i, j, k, real) per the Adafruit library.
    We repack as (w, x, y, z) for clarity in the payload.
    Returns dict or None on failure.
    """
    try:
        i, j, k, real = imu.quaternion
        if any(v is None for v in (i, j, k, real)):
            return None
        return {
            "w": round(real, 6),
            "x": round(i,    6),
            "y": round(j,    6),
            "z": round(k,    6),
        }
    except Exception as e:
        print(f"IMU read error: {e}")
        return None


def mock_quaternion():
    """Identity quaternion for testing without hardware."""
    return {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}


# ─────────────────────────────────────────────
#  Quaternion Averaging
#  Simple component-wise mean then renormalize.
#  Valid for small rotational variance (which a
#  held wand over one publish window will have).
# ─────────────────────────────────────────────

def average_quaternions(samples):
    """
    Average a list of {"w","x","y","z"} dicts and renormalize.
    Handles quaternion double-cover: if a sample's dot product
    with the first sample is negative, flip it before averaging.
    """
    if not samples:
        return None

    import math

    ref = samples[0]
    aw = ax = ay = az = 0.0

    for q in samples:
        # Ensure we pick the shorter arc (double-cover fix).
        dot = ref["w"]*q["w"] + ref["x"]*q["x"] + ref["y"]*q["y"] + ref["z"]*q["z"]
        sign = 1.0 if dot >= 0.0 else -1.0
        aw += sign * q["w"]
        ax += sign * q["x"]
        ay += sign * q["y"]
        az += sign * q["z"]

    n = len(samples)
    aw /= n; ax /= n; ay /= n; az /= n

    mag = math.sqrt(aw*aw + ax*ax + ay*ay + az*az)
    if mag < 1e-9:
        return {"w": 1.0, "x": 0.0, "y": 0.0, "z": 0.0}

    return {
        "w": round(aw / mag, 6),
        "x": round(ax / mag, 6),
        "y": round(ay / mag, 6),
        "z": round(az / mag, 6),
    }


# ─────────────────────────────────────────────
#  MQTT Publisher  (unchanged structure from
#  your existing IMUPublisher class)
# ─────────────────────────────────────────────

class IMUPublisher:
    def __init__(self, endpoint, cert_path, key_path, ca_path, client_id):
        self.endpoint  = endpoint
        self.cert_path = cert_path
        self.key_path  = key_path
        self.ca_path   = ca_path
        self.client_id = client_id
        self.connection = None
        self.connected  = False

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
                keep_alive_secs=30,
            )
            self.connection.connect().result()
            self.connected = True
            print("Connected to AWS IoT Core!")
        except Exception as e:
            print(f"Connection failed: {e}")
            self.connected = False

    def publish_combined(self, topic, tip_quat, base_quat, tip_samples, base_samples):
        """Publish combined tip and base quaternions in a single message."""
        if not self.connected or not self.connection:
            return False
        try:
            payload = json.dumps({
                "timestamp": int(time.time() * 1000),
                "client_id": self.client_id,
                "data": {
                    "tip": {
                        "quaternion": tip_quat,
                        "sample_count": tip_samples,
                    },
                    "base": {
                        "quaternion": base_quat,
                        "sample_count": base_samples,
                    }
                }
            })
            self.connection.publish(
                topic=topic,
                payload=payload,
                qos=mqtt.QoS.AT_LEAST_ONCE,
            )
            return True
        except Exception as e:
            print(f"Publish error on {topic}: {e}")
            self.connected = False
            return False

    def disconnect(self):
        if self.connection:
            try:
                self.connection.disconnect().result()
                print("Disconnected from AWS IoT Core.")
            except Exception as e:
                print(f"Disconnection error: {e}")
        self.connected = False


# ─────────────────────────────────────────────
#  Main Loop
# ─────────────────────────────────────────────

def main():
    publisher = IMUPublisher(
        endpoint=IOT_ENDPOINT,
        cert_path=CERT_PATH,
        key_path=KEY_PATH,
        ca_path=CA_PATH,
        client_id=CLIENT_ID,
    )
    publisher.connect()

    if not publisher.connected:
        print("Failed to connect to MQTT. Exiting.")
        return

    print(f"\nPublishing combined wand data:")
    print(f"  Topic: {TOPIC_WAND}")
    print(f"  Tip  (bus 8)  + Base (bus 10)")
    print(f"  Sample rate: {SAMPLE_RATE_HZ} Hz  |  Publish rate: {PUBLISH_RATE_HZ} Hz")
    print("Press Ctrl+C to stop.\n")

    publish_interval = 1.0 / PUBLISH_RATE_HZ
    sample_interval  = 1.0 / SAMPLE_RATE_HZ

    buf_tip  = []
    buf_base = []
    last_publish = time.time()
    message_count = 0

    try:
        while True:
            # ── Sample both IMUs ─────────────────────────────────────────
            if IMU_AVAILABLE:
                q_tip  = read_quaternion(imu_tip)
                q_base = read_quaternion(imu_base)
            else:
                q_tip  = mock_quaternion()
                q_base = mock_quaternion()

            if q_tip:
                buf_tip.append(q_tip)
            if q_base:
                buf_base.append(q_base)

            # ── Publish averaged quaternions at publish rate ──────────────
            now = time.time()
            if now - last_publish >= publish_interval:
                if buf_tip and buf_base:
                    avg_tip  = average_quaternions(buf_tip)
                    avg_base = average_quaternions(buf_base)

                    # Publish combined message to single topic
                    ok = publisher.publish_combined(
                        TOPIC_WAND, avg_tip, avg_base, len(buf_tip), len(buf_base)
                    )

                    if ok:
                        message_count += 1
                        print(
                            f"[{message_count}] "
                            f"TIP  w={avg_tip['w']:+.4f} x={avg_tip['x']:+.4f} "
                            f"y={avg_tip['y']:+.4f} z={avg_tip['z']:+.4f} "
                            f"({len(buf_tip)} samples) | "
                            f"BASE w={avg_base['w']:+.4f} x={avg_base['x']:+.4f} "
                            f"y={avg_base['y']:+.4f} z={avg_base['z']:+.4f} "
                            f"({len(buf_base)} samples)"
                        )

                    buf_tip  = []
                    buf_base = []
                    last_publish = now

            time.sleep(sample_interval)

    except KeyboardInterrupt:
        print("\nStopping IMU publisher...")
    finally:
        publisher.disconnect()
        print(f"Total messages published: {message_count}")


if __name__ == "__main__":
    main()
