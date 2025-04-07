import requests
import os
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import random
from datetime import datetime, timedelta
from google import genai
import re
from typing import Dict, Any

load_dotenv()

# Google Calendar API Scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.events']


def search_restaurants(location: str, cuisine: str):
    """Search restaurants using Google Places API."""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{cuisine} restaurants in {location}",
        "key": os.getenv("GOOGLE_PLACES_API_KEY")
    }
    response = requests.get(url, params=params)
    return response.json()

def parse_google_maps_results(api_response):
    """Extracts key restaurant details from Google Maps API response."""
    restaurants = []
    for place in api_response.get('results', [])[:3]:  # Top 3 results
        restaurant = {
            "name": place.get("name"),
            "address": place.get("formatted_address"),
            "rating": place.get("rating"),
            "price_level": place.get("price_level", "N/A"),
            "opening_hours": "Open" if place.get("opening_hours", {}).get("open_now") else "Closed"
        }
        restaurants.append(restaurant)
    return restaurants

def mock_book_restaurant(restaurant_name: str, guests: int):
    """Simulates a reservation with mock data."""
    reservation_id = f"RES-{random.randint(1000, 9999)}"
    reservation_time = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT19:00:00")
    
    return {
        "status": "confirmed",
        "restaurant": restaurant_name,
        "reservation_id": reservation_id,
        "time": reservation_time,
        "guests": guests
    }

# Example usage:
# api_response = search_restaurants("Toronto", "Indian")
# Extracting key restaurant details
# restaurants = parse_google_maps_results(api_response)
# Book the restaurant for the highest rating
# print(restaurants[0]['name'])

# Example usage:
# booking = mock_book_restaurant(restaurants[0]['name'], guests=2)
# print(booking)
# {'status': 'confirmed', 'restaurant': 'Angara Indian and Hakka downtown', 'reservation_id': 'RES-8609', 'time': '2025-04-08T19:00:00', 'guests': 2}

def authenticate_google_calendar():
    """Handles OAuth 2.0 flow and returns credentials."""
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def create_calendar_event(summary: str, location: str, start_time: str, guests: int = 2):
    """Creates a Google Calendar event."""
    creds = authenticate_google_calendar()
    service = build('calendar', 'v3', credentials=creds)
    
    end_time = (datetime.fromisoformat(start_time) + timedelta(hours=2))
    
    event = {
        'summary': summary,
        'location': location,
        'start': {
            'dateTime': start_time,
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'America/New_York',
        },
        'attendees': [{'email': f'guest{i+1}@example.com'} for i in range(guests)],
        'reminders': {
            'useDefault': True,
        },
    }
    
    event = service.events().insert(
        calendarId='primary',
        body=event
    ).execute()
    
    return {
        'event_id': event['id'],
        'html_link': event['htmlLink'],
        'hangout_link': event.get('hangoutLink', '')
    }

# Update your mock_book_restaurant function to include calendar integration
def book_and_schedule(restaurant_name: str, address: str, guests: int = 2):
    """Combines booking and calendar scheduling."""
    # Step 1: Mock booking
    booking = mock_book_restaurant(restaurant_name, guests)
    
    # Step 2: Add to Google Calendar
    calendar_event = create_calendar_event(
        summary=f"Dinner at {restaurant_name}",
        location=address,
        start_time=booking['time'],
        guests=guests
    )
    
    return {
        'booking': booking,
        'calendar_event': calendar_event
    }


# EXAMPLE DEBUGGING

# api_response = search_restaurants("Toronto", "Indian")
# restaurants = parse_google_maps_results(api_response)

# if restaurants:
#     selected_restaurant = restaurants[0]
#     result = book_and_schedule(
#         restaurant_name=selected_restaurant['name'],
#         address=selected_restaurant['address'],
#         guests=2
#     )
    
#     print("\n🎉 Booking Confirmed!")
#     print(f"Restaurant: {result['booking']['restaurant']}")
#     print(f"Reservation ID: {result['booking']['reservation_id']}")
#     print(f"Time: {result['booking']['time']}")
#     print(f"Calendar Event: {result['calendar_event']['html_link']}")
# else:
#     print("No restaurants found.")


# OUTPUT

# 🎉 Booking Confirmed!
# Restaurant: The Grand Indian Dining
# Reservation ID: RES-3324
# Time: 2025-04-08T19:00:00
# Calendar Event: https://www.google.com/calendar/event?eid=dnNzMnNkNm11dG5janJwbTIyNW03cGpqMTAgbXVkYXNzYXI3ODZtb3N1QG0

