import paho.mqtt.publish as publish
from mfrc522 import MFRC522
import time

reader = MFRC522()
MQTT_BROKER = "localhost"
MQTT_TOPIC = "rfid/new_card"  # Topic for new card readings

def main():
    while True:
        (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)
        if status == reader.MI_OK:
            (status, uid) = reader.MFRC522_Anticoll()
            if status == reader.MI_OK:
                card_id = '-'.join([str(x) for x in uid])
                publish.single(MQTT_TOPIC, card_id, hostname=MQTT_BROKER)
                time.sleep(1)
        time.sleep(0.1)

if __name__ == "__main__":
    main()