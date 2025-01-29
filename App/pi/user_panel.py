import requests
import json
import time
import RPi.GPIO as GPIO
from mfrc522 import MFRC522
import lib.oled.SSD1331 as SSD1331
from PIL import Image, ImageDraw, ImageFont

BUZZER_PIN = 23

# API Configuration
API_BASE_URL = "http://192.168.0.107:8000/api"
SEARCH_GYM_CARD_URL = f"{API_BASE_URL}/search_gym_card/"
UPDATE_GYM_CARD_URL = f"{API_BASE_URL}/update_gym_card/"

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

# OLED Display Initialization
disp = SSD1331.SSD1331()
disp.Init()
disp.clear()



def beep():
    """Short buzzer beep for feedback."""
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(BUZZER_PIN, GPIO.HIGH)


def display_message(line1, line2="", duration=3):
    """Display message on OLED."""
    image = Image.new("RGB", (disp.width, disp.height), "BLACK")
    draw = ImageDraw.Draw(image)
    draw.text((8, 0), line1, fill="WHITE")
    if line2:
        draw.text((12, 40), line2, fill="WHITE")
    disp.ShowImage(image, 0, 0)
    time.sleep(duration)
    disp.clear()


def fetch_card_details(card_id):
    """Fetch card details from API."""
    payload = {"search_by": "rfid_card_id", "search_term": card_id}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(SEARCH_GYM_CARD_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("gym_cards"):
                return data["gym_cards"][0]  # Return first found card
        return None
    except requests.RequestException as e:
        print(f"API Error: {e}")
        return None


def update_card_status(card_id, new_status):
    """Update gym card status via API."""
    payload = {"id": card_id, "status": new_status}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(UPDATE_GYM_CARD_URL, json=payload, headers=headers)
        return response.json()
    except requests.RequestException as e:
        print(f"API Error: {e}")
        return {"status": "error", "message": "API request failed"}


def read_rfid():
    """Reads an RFID card and returns its ID."""
    reader = MFRC522()
    while True:
        status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)
        if status == reader.MI_OK:
            status, uid = reader.MFRC522_Anticoll()
            if status == reader.MI_OK:
                return "-".join(str(x) for x in uid)


def main():
    while True:
        display_message("Scan Your Card", "", duration=0)
        card_id = read_rfid()
        beep()

        card_info = fetch_card_details(card_id)

        if not card_info:
            display_message("Card Not Found", "Try Again")
            continue

        card_status = card_info.get("Status", "").lower()
        card_db_id = card_info.get("id")
        card_priority = card_info.get("priority", 10)  # Default priority to 1 if not provided

        if card_priority == 0:
            display_message("Redirecting", "To Admin Panel", 3)
            """Redirect to Admin Panel"""
            continue

        if card_status == "inactive":
            display_message("Access Denied", "Inactive Card", 3)
            continue

        new_status = "in" if card_status == "active" else "active"
        response = update_card_status(card_db_id, new_status)

        if response.get("status") == "success":
            message = "Welcome" if new_status == "in" else "Bye Bye"
            display_message(message, "", 3)
        else:
            display_message("Update Failed", response.get("message", "Error"), 3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        GPIO.cleanup()
        disp.clear()