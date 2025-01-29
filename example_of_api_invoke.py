import requests
import json

def test_search_gym_card():
    url = "http://192.168.0.107:8000/api/search_gym_card/"
    
    payload = {
        "search_by": "rfid_card_id",
        "search_term": "14656516846"
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('gym_cards'):
                print("\nFound gym cards:")
                for card in data['gym_cards']:
                    print(f"\nCard ID: {card.get('id')}")
                    print(f"RFID: {card.get('rfid_card_id')}")
                    print(f"Title: {card.get('Title')}")
                    print(f"Status: {card.get('Status')}")
            else:
                print("No cards found")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_search_gym_card()
