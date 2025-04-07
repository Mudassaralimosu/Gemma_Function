import os
import json
import random
import requests
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import google.genai as genai


# Load environment variables
load_dotenv()

# === CONFIG ===
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
GEMMA_API_KEY = os.getenv("GEMINI_API")

# === GEMMA SETUP ===
client = genai.Client(api_key=GEMMA_API_KEY)
model_id = "gemma-3-27b-it"
chat = client.chats.create(model=model_id)

# === TOOL FUNCTIONS ===
def find_restaurants(location: str, cuisine: str, max_price: int = None):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    query = f"{cuisine} restaurants in {location}"
    params = {"query": query, "key": GOOGLE_PLACES_API_KEY}
    response = requests.get(url, params=params).json()

    restaurants = []
    for place in response.get('results', [])[:3]:
        price_level = place.get("price_level", 0)
        if max_price is None or price_level <= max_price:
            restaurants.append({
                "name": place.get("name"),
                "address": place.get("formatted_address"),
                "rating": place.get("rating"),
                "price_level": price_level,
                "open": place.get("opening_hours", {}).get("open_now", False)
            })
    return restaurants

def make_reservation(restaurant_name: str, guests: int):
    reservation_id = f"RES-{random.randint(1000,9999)}"
    reservation_time = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT19:00:00")
    return {
        "status": "confirmed",
        "restaurant": restaurant_name,
        "reservation_id": reservation_id,
        "time": reservation_time,
        "guests": guests
    }

def authenticate_google_calendar():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def schedule_calendar_event(summary: str, location: str, start_time: str, guests: int):
    creds = authenticate_google_calendar()
    service = build('calendar', 'v3', credentials=creds)
    end_time = (datetime.fromisoformat(start_time) + timedelta(hours=2)).isoformat()

    event = {
        'summary': summary,
        'location': location,
        'start': {'dateTime': start_time, 'timeZone': 'America/New_York'},
        'end': {'dateTime': end_time, 'timeZone': 'America/New_York'},
        'attendees': [{'email': f'guest{i+1}@example.com'} for i in range(guests)],
        'reminders': {'useDefault': True},
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return {
        'event_id': created_event['id'],
        'html_link': created_event['htmlLink'],
        'hangout_link': created_event.get('hangoutLink', '')
    }

# # === GEMMA FUNCTION EXECUTOR ===

def run_chat(user_input):
    prompt = f'''
You have access to functions. If you decide to invoke any of the function(s),
you MUST put it in the format of
{{"name": function_name, "parameters": dictionary_of_argument_name_and_value}}

You SHOULD NOT include any other text in the response if you call a function.

Here are the available functions:

{{"name": "find_restaurants", "parameters": {{"location": "string", "cuisine": "string", "max_price": "int"}}}}
{{"name": "make_reservation", "parameters": {{"restaurant_name": "string", "guests": "int"}}}}
{{"name": "schedule_calendar_event", "parameters": {{"summary": "string", "location": "string", "start_time": "string", "guests": "int"}}}}

You are asked to fulfill the user's request. Here's what to do:

1. Find restaurants based on the user’s input (location, cuisine, and price).
2. Once you find a restaurant, make a reservation.
3. After confirming the reservation, schedule a calendar event.

User: {user_input}
'''
    # Send user input to Gemma
    response = chat.send_message(prompt)
    print("\nGemma Response:\n", response.text)
    
    # Parse the Gemma response to detect function calls
    try:
        tool_call = json.loads(response.text.strip())
        print("\nTool Call Parsed:\n", tool_call)
        
        func_name = tool_call.get("name")
        params = tool_call.get("parameters")
        
        if func_name == "find_restaurants":
            result = find_restaurants(**params)
            if result:
                # Assuming Gemma should also call make_reservation next
                reservation = make_reservation(result[0]["name"], 2)  # Example: 2 guests
                # After reservation, schedule the calendar event
                event = schedule_calendar_event("Dinner at " + result[0]["name"], result[0]["address"], reservation["time"], 2)
                # Print results in a user-friendly way
                print("\nStep 1: Restaurants Found:")
                for idx, restaurant in enumerate(result, 1):
                    print(f"{idx}. {restaurant['name']} - {restaurant['rating']} stars, Price Level: {restaurant['price_level']}")
                    print(f"   Address: {restaurant['address']}")
                    print(f"   Open Now: {'Yes' if restaurant['open'] else 'No'}\n")

                print("\nStep 2: Reservation Confirmation:")
                print(f"Reservation made at {reservation['restaurant']} for {reservation['guests']} guests.")
                print(f"Reservation ID: {reservation['reservation_id']}")
                print(f"Reservation Time: {reservation['time']}\n")

                print("\nStep 3: Calendar Event Scheduled:")
                print(f"Event created: Dinner at {reservation['restaurant']}")
                print(f"Event Time: {reservation['time']}")
                print(f"View Event: {event['html_link']}")
                if event['hangout_link']:
                    print(f"Hangout Link: {event['hangout_link']}")
        elif func_name == "make_reservation":
            result = make_reservation(**params)
            print(f"\nReservation Confirmation:")
            print(f"Reservation made at {result['restaurant']} for {result['guests']} guests.")
            print(f"Reservation ID: {result['reservation_id']}")
            print(f"Reservation Time: {result['time']}")
        elif func_name == "schedule_calendar_event":
            result = schedule_calendar_event(**params)
            print(f"\nCalendar Event Scheduled:")
            print(f"Event created: {params['summary']}")
            print(f"Event Time: {params['start_time']}")
            print(f"View Event: {result['html_link']}")
            if result['hangout_link']:
                print(f"Hangout Link: {result['hangout_link']}")
        else:
            result = f"Error: Unrecognized function {func_name}"
        
    except json.JSONDecodeError as e:
        print(f"Error parsing Gemma response: {e}")


if __name__ == '__main__':
    user_request = "Book me a 7pm dinner for 2 at a Japanese restaurant in NYC under $100, then add it to my calendar"
    run_chat(user_request)



# OUTPUT


# Gemma Response:
#  {"name": "find_restaurants", "parameters": {"location": "NYC", "cuisine": "Japanese", "max_price": 100}}


# Tool Call Parsed:
#  {'name': 'find_restaurants', 'parameters': {'location': 'NYC', 'cuisine': 'Japanese', 'max_price': 100}}

# Step 1: Restaurants Found:
# 1. Izakaya MEW - 4.5 stars, Price Level: 2
#    Address: 53 W 35th St, New York, NY 10001, United States
#    Open Now: No

# 2. Sakagura - 4.5 stars, Price Level: 3
#    Address: 211 E 43rd St B1, New York, NY 10017, United States
#    Open Now: No

# 3. Zuma New York - 4.3 stars, Price Level: 4
#    Address: 261 Madison Ave, New York, NY 10016, United States
#    Open Now: No


# Step 2: Reservation Confirmation:
# Reservation made at Izakaya MEW for 2 guests.
# Reservation ID: RES-7494
# Reservation Time: 2025-04-08T19:00:00


# Step 3: Calendar Event Scheduled:
# Event created: Dinner at Izakaya MEW
# Event Time: 2025-04-08T19:00:00
# View Event: https://www.google.com/calendar/event?eid=cWQzbGQ1YjRjazhsbXV1YTduYWYycjUyam8gbXVkYXNzYXI3ODZtb3N1QG0