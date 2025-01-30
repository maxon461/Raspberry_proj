import requests
import json
import time
import RPi.GPIO as GPIO
from mfrc522 import MFRC522
import lib.oled.SSD1331 as SSD1331
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# GPIO Pins
LED1, LED2, LED3, LED4 = 13, 12, 19, 26
buttonRed, buttonGreen = 5, 6
encoderLeft, encoderRight = 17, 27
BUZZER_PIN = 23

# API URLs
API_BASE_URL = "http://192.168.0.107:8000/api"
SEARCH_GYM_CARD_URL = f"{API_BASE_URL}/search_gym_card/"
UPDATE_GYM_CARD_URL = f"{API_BASE_URL}/update_gym_card/"
CREATE_GYM_CARD_URL = f"{API_BASE_URL}/create_gym_card/"
DELETE_GYM_CARD_URL = f"{API_BASE_URL}/delete_gym_card/"

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup([LED1, LED2, LED3, LED4, BUZZER_PIN], GPIO.OUT)
GPIO.setup([buttonRed, buttonGreen, encoderLeft, encoderRight], GPIO.IN, pull_up_down=GPIO.PUD_UP)

# OLED Setup
disp = SSD1331.SSD1331()
disp.Init()
disp.clear()
fontLarge = ImageFont.truetype("./lib/oled/Font.ttf", 20)
fontSmall = ImageFont.truetype("./lib/oled/Font.ttf", 13)

# RFID Reader
reader = MFRC522()


def beep():
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(BUZZER_PIN, GPIO.HIGH)


def display_message(line1, line2="", duration=3):
    """Display a message on OLED"""
    image = Image.new("RGB", (disp.width, disp.height), "BLACK")
    draw = ImageDraw.Draw(image)
    draw.text((8, 0), line1, font=fontLarge, fill="WHITE")
    if line2:
        draw.text((12, 40), line2, font=fontSmall, fill="WHITE")
    disp.ShowImage(image, 0, 0)
    time.sleep(duration)
    disp.clear()


def fetch_card_details(card_id):
    """Fetch gym card details from API"""
    payload = {"search_by": "rfid_card_id", "search_term": card_id}
    try:
        response = requests.post(SEARCH_GYM_CARD_URL, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            data = response.json()
            return data["gym_cards"][0] if data.get("gym_cards") else None
    except requests.RequestException as e:
        print(f"API Error: {e}")
    return None


def update_card_status(card_id, new_status):
    """Update gym card status"""
    payload = {"id": card_id, "status": new_status}
    try:
        response = requests.post(UPDATE_GYM_CARD_URL, json=payload, headers={"Content-Type": "application/json"})
        return response.json()
    except requests.RequestException as e:
        print(f"API Error: {e}")
    return {"status": "error", "message": "API request failed"}


def read_rfid():
    """Reads an RFID card"""
    while True:
        status, _ = reader.MFRC522_Request(reader.PICC_REQIDL)
        if status == reader.MI_OK:
            status, uid = reader.MFRC522_Anticoll()
            if status == reader.MI_OK:
                return "-".join(str(x) for x in uid)


def create_gym_card(rfid_card_id):
    """Create a new gym card"""
    payload = {
        "title": "New Gym Card",
        "description": "Created from Admin Panel",
        "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "rfid_card_id": rfid_card_id,
        "priority": 1
    }
    response = requests.post(CREATE_GYM_CARD_URL, json=payload, headers={"Content-Type": "application/json"})
    return response.json()


def delete_gym_card(card_id):
    """Delete a gym card"""
    payload = {"id": card_id}
    response = requests.post(DELETE_GYM_CARD_URL, json=payload, headers={"Content-Type": "application/json"})
    return response.json()


def admin_panel():
    """Admin Panel Navigation"""
    options = ["Create Card", "Delete Card", "Exit"]
    index = 0
    last_state_left = GPIO.input(encoderLeft)
    last_state_right = GPIO.input(encoderRight)

    while True:
        # Format options to show cursor (->) on the selected option
        option_lines = ["-> " + options[i] if i == index else "   " + options[i] for i in range(len(options))]
        display_message(option_lines[0], option_lines[1] if len(options) > 1 else "")

        # Check for rotary encoder movement
        current_state_left = GPIO.input(encoderLeft)
        current_state_right = GPIO.input(encoderRight)

        if last_state_left == GPIO.HIGH and current_state_left == GPIO.LOW:
            index = (index - 1) % len(options)  # Rotate Left: Move Up
            beep()

        if last_state_right == GPIO.HIGH and current_state_right == GPIO.LOW:
            index = (index + 1) % len(options)  # Rotate Right: Move Down
            beep()

        last_state_left = current_state_left
        last_state_right = current_state_right

        # Check for button press to confirm selection
        if GPIO.input(buttonRed) == GPIO.LOW or GPIO.input(buttonGreen) == GPIO.LOW:
            beep()
            if index == 2:  # Exit
                display_message("Exiting Admin", "Returning to User Panel", 3)
                return

            display_message("Scan Card", "To Proceed")
            card_id = read_rfid()

            if index == 0:  # Create Card
                GPIO.output(LED1, GPIO.HIGH)
                response = create_gym_card(card_id)
                message = "Card Created" if response.get("status") == "success" else "Failed"
                GPIO.output(LED1, GPIO.LOW)

            elif index == 1:  # Delete Card
                GPIO.output(LED2, GPIO.HIGH)
                response = delete_gym_card(card_id)
                message = "Card Deleted" if response.get("status") == "success" else "Failed"
                GPIO.output(LED2, GPIO.LOW)

            display_message(message, "", 3)


def main():
    while True:
        display_message("Scan Your Card", "")
        card_id = read_rfid()
        beep()

        card_info = fetch_card_details(card_id)
        if not card_info:
            display_message("Card Not Found", "Try Again", 3)
            continue

        card_status = card_info.get("Status", "").lower()
        card_db_id = card_info.get("id")
        card_priority = card_info.get("priority", 1)

        if card_priority == 0:
            display_message("Redirecting", "To Admin Panel", 3)
            admin_panel()
            continue

        new_status = "in" if card_status == "active" else "active"
        response = update_card_status(card_db_id, new_status)
        message = "Welcome" if new_status == "in" else "Bye Bye"
        display_message(message if response.get("status") == "success" else "Update Failed", "", 3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        GPIO.cleanup()
        disp.clear()
