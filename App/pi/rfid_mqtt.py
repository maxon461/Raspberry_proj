import RPi.GPIO as GPIO
import time
import paho.mqtt.publish as publish
import sys
from mfrc522 import MFRC522
import json

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

led1, buzzerPin = 13, 23
GPIO.setup(led1, GPIO.OUT)
GPIO.setup(buzzerPin, GPIO.OUT)
GPIO.output(buzzerPin, 1)

# MQTT Configuration
MQTT_BROKER = "127.0.0.1"
MQTT_TOPIC = "rfid/cards"

# Initialize RFID reader
reader = MFRC522()

# Test MQTT connection
try:
    publish.single(MQTT_TOPIC, "Test connection", hostname=MQTT_BROKER)
    print("MQTT Connected")
except Exception as e:
    print(f"MQTT Error: {e}")
    sys.exit(1)

print("Waiting for cards...")
current_card = None
no_card_count = 0
CARD_HOLD_THRESHOLD = 3  # Must detect the card this many times before registering it
hold_count = 0

try:
    while True:
        (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)

        if status != reader.MI_OK:
            no_card_count += 1
            if no_card_count >= CARD_HOLD_THRESHOLD:
                current_card = None
                no_card_count = 0
                hold_count = 0  # Reset hold count
            time.sleep(0.1)
            continue

        no_card_count = 0
        (status, uid) = reader.MFRC522_Anticoll()
        if status != reader.MI_OK:
            continue

        card_id = '-'.join([str(x) for x in uid])

        if current_card != card_id:
            hold_count += 1
            if hold_count < CARD_HOLD_THRESHOLD:
                time.sleep(0.1)
                continue  # Wait for the card to be held long enough

            current_card = card_id
            GPIO.output(led1, GPIO.HIGH)
            GPIO.output(buzzerPin, 0)
            time.sleep(0.1)
            GPIO.output(buzzerPin, 1)
            GPIO.output(led1, GPIO.LOW)

            try:
                publish.single(MQTT_TOPIC, json.dumps({"card_id": "14656516846"}), hostname=MQTT_BROKER)
                print(f"Read card: {card_id}")
            except Exception as e:
                print(f"MQTT Error: {e}")

        reader.MFRC522_StopCrypto1()
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopping...")
except Exception as e:
    print(f"Error: {e}")
finally:
    GPIO.cleanup()
