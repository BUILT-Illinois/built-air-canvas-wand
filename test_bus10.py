# test_bus10.py
from adafruit_extended_bus import ExtendedI2C as I2C
from adafruit_bno08x.i2c import BNO08X_I2C
from adafruit_bno08x import BNO_REPORT_ROTATION_VECTOR
import time

print("Opening bus 10...")
i2c = I2C(10)
print("Creating BNO object...")
imu = BNO08X_I2C(i2c, address=0x4A)
print("BNO object created. Sleeping 3s...")
time.sleep(3)
print("Enabling feature...")
imu.enable_feature(BNO_REPORT_ROTATION_VECTOR)
print("SUCCESS — reading quaternion:")
print(imu.quaternion)
