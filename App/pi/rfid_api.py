#!/usr/bin/env python3
import RPi.GPIO as GPIO
import requests
import json
from mfrc522 import MFRC522
import time
from datetime import datetime, timedelta

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Define pins
LED_GREEN = 13  # Success
LED_RED = 12  # Error
BUZZER = 23

# Setup pins
for pin in [LED_GREEN, LED_RED, BUZZER]:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Initialize RFID reader
reader = MFRC522()

# Django API endpoints
BASE_URL = "http://your-django-server:8000/api"
ENDPOINTS = {
    'create': f"{BASE_URL}/create_gym_card/",
    'delete': f"{BASE_URL}/delete_gym_card/",
    'update': f"{BASE_URL}/update_gym_card/"
}


def signal_feedback(success=True):
    """Visual and audio feedback"""
    led_pin = LED_GREEN if success else LED_RED
    GPIO.output(led_pin, GPIO.HIGH)
    GPIO.output(BUZZER, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(BUZZER, GPIO.LOW)
    time.sleep(0.5)
    GPIO.output(led_pin, GPIO.LOW)


def send_request(endpoint, data):
    """Send request to Django server"""
    try:
        response = requests.post(
            endpoint,
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return None


def create_card(card_id):
    """Create new card with RFID"""
    data = {
        'title': f'Card {card_id}',
        'description': f'RFID Card created from Raspberry Pi',
        'expiration_date': (datetime.now() + timedelta(days=365)).isoformat(),
        'priority': 0
    }

    response = send_request(ENDPOINTS['create'], data)
    if response and response.get('status') == 'success':
        print(f"Created card: {response.get('card', {}).get('Title')}")
        signal_feedback(True)
    else:
        print("Error creating card")
        signal_feedback(False)


def update_card_status(card_id, new_status):
    """Update card status"""
    data = {
        'id': card_id,
        'status': new_status
    }

    response = send_request(ENDPOINTS['update'], data)
    if response and response.get('status') == 'success':
        print(f"Updated card status to: {new_status}")
        signal_feedback(True)
    else:
        print("Error updating card")
        signal_feedback(False)


def delete_card(card_id):
    """Delete card"""
    data = {
        'id': card_id
    }

    response = send_request(ENDPOINTS['delete'], data)
    if response and response.get('status') == 'success':
        print("Card deleted successfully")
        signal_feedback(True)
    else:
        print("Error deleting card")
        signal_feedback(False)


def get_all_cards():
    """Get all cards (useful for checking if card exists)"""
    response = send_request(ENDPOINTS['get_all'], {})
    if response and 'gym_cards' in response:
        return response['gym_cards']
    return []


def main():
    print("RFID Reader Started")
    print("Commands:")
    print("1 - Register new card")
    print("2 - Update card status (in/out)")
    print("3 - Delete card")
    print("Ctrl+C to exit")

    mode = '1'  # Default mode is register

    try:
        while True:
            # Check for command input
            cmd = input("Enter command (1-3): ")
            if cmd in ['1', '2', '3']:
                mode = cmd
                print(f"Mode: {['Register', 'Update', 'Delete'][int(mode) - 1]}")
                print("Present card...")

                # Wait for card
                while True:
                    (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)

                    if status == reader.MI_OK:
                        (status, uid) = reader.MFRC522_Anticoll()
                        if status == reader.MI_OK:
                            card_id = '-'.join([str(x) for x in uid])
                            print(f"Card detected: {card_id}")

                            if mode == '1':
                                create_card(card_id)
                            elif mode == '2':
                                # Toggle status between active/deactivated
                                update_card_status(card_id, 'active')
                            elif mode == '3':
                                delete_card(card_id)

                            break  # Return to mode selection

                    time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()