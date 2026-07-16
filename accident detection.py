import serial
import time
import telebot
import smbus2
import math

# ========================
# CONFIG
# ========================
TOKEN = "# Replace with your bot token" 
CHAT_ID = "# Replace with your chat ID"            
bot = telebot.TeleBot(TOKEN)

# MPU6050 setup
bus = smbus2.SMBus(1)
MPU_ADDR = 0x68
bus.write_byte_data(MPU_ADDR, 0x6B, 0)  # Wake up MPU6050

# GPS setup
gps_serial = serial.Serial("/dev/serial0", baudrate=9600, timeout=1)

# ========================
# HELPER FUNCTIONS
# ========================
def read_mpu6050():
    acc_x = read_word_2c(0x3B)
    acc_y = read_word_2c(0x3D)
    acc_z = read_word_2c(0x3F)

    # Calculate overall acceleration (g force)
    total_acc = math.sqrt(acc_x**2 + acc_y**2 + acc_z**2) / 16384.0
    return total_acc

def read_word_2c(addr):
    high = bus.read_byte_data(MPU_ADDR, addr)
    low = bus.read_byte_data(MPU_ADDR, addr+1)
    val = (high << 8) + low
    if val >= 0x8000:
        val = -((65535 - val) + 1)
    return val

def get_gps_location():
    while True:
        line = gps_serial.readline().decode('utf-8', errors='ignore')
        if line.startswith("$GPGGA"):  # GPS data line
            parts = line.split(",")
            if len(parts) > 5 and parts[2] != "" and parts[4] != "":
                lat = convert_to_degrees(parts[2])
                lon = convert_to_degrees(parts[4])
                return lat, lon
    return None, None

def convert_to_degrees(raw_val):
    # Convert GPS format (ddmm.mmmm) to decimal degrees
    raw_val = float(raw_val)
    degrees = int(raw_val / 100)
    minutes = raw_val - (degrees * 100)
    return degrees + (minutes / 60)

# ========================
# MAIN LOOP
# ========================
print("Monitoring for accidents...")
while True:
    try:
        acc = read_mpu6050()
        print("Acceleration:", acc)

        if acc > 3:  # Threshold for accident detection
            print("🚨 Accident Detected!")
            lat, lon = get_gps_location()
            if lat and lon:
                msg = f"🚨 Accident detected!\nLocation: https://www.google.com/maps?q={lat},{lon}"
                bot.send_message(CHAT_ID, msg)
                print("Message sent to Telegram!")
            else:
                print("GPS not fixed yet...")
            time.sleep(10)  # avoid spamming
    except Exception as e:
        print("Error:", e)
        time.sleep(2)
