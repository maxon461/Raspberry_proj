import paho.mqtt.client as mqtt
import json
import time
import argparse

def send_rfid_card(card_id):
    try:
        # Create MQTT client
        client = mqtt.Client(protocol=mqtt.MQTTv311)
        
        # Connect to broker
        print("Connecting to MQTT broker...")
        client.connect("localhost", 1883, 60)
        
        # Prepare message
        message = json.dumps({"card_id": card_id})
        
        # Publish message
        print(f"Sending RFID card ID: {card_id}")
        client.publish("rfid/cards", message)
        
        # Wait for message to be sent
        time.sleep(1)
        
        # Disconnect
        client.disconnect()
        print("Message sent successfully")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Send test RFID card data via MQTT')
    parser.add_argument('card_id', type=str, help='RFID card ID to send')
    
    args = parser.parse_args()
    send_rfid_card(args.card_id)
