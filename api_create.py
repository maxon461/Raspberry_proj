import requests
import json
from datetime import datetime, timedelta

def test_create_gym_card():
    url = "http://192.168.0.107:8000/api/create_gym_card/"
    
    # Create test data
    payload = {
        "title": "Test Gym Card",
        "description": "Test Description",
        "expiration_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "rfid_card_id": "14656516846",
        "priority": 1
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nCreated gym card:")
            print(f"Status: {data.get('status')}")
            print(f"Message: {data.get('message')}")
            if 'card' in data:
                card = data['card']
                print("\nCard Details:")
                print(f"ID: {card.get('id')}")
                print(f"Title: {card.get('Title')}")
                print(f"Description: {card.get('Description')}")
                print(f"RFID: {card.get('rfid_card_id')}")
                print(f"Status: {card.get('Status')}")
                print(f"Priority: {card.get('Priority')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_create_gym_card()
