# 🍣 Gemma Function Calling API Orchestration

This project demonstrates how to use **Google DeepMind's Gemma model** to perform **function calling and orchestration** across multiple APIs — combining Google Places, mock restaurant reservations, and Google Calendar — to book dinner reservations intelligently based on natural language input.

## ✨ Features

- 🔍 **Restaurant Search** using Google Places API
- 🍽️ **Mock Reservation System** for restaurant bookings
- 📅 **Google Calendar Integration** to schedule dining events
- 🧠 **Gemma 3 Model Function Calling** to understand user intent and chain function calls automatically

## 📦 Requirements

- Python 3.8+
- Google Places API Key
- Google Calendar API credentials
- Gemini (Gemma) API Key

## 🔐 Environment Setup

Create a `.env` file in the root directory with the following:

```env
GOOGLE_PLACES_API_KEY=your_google_places_api_key
GEMINI_API=your_gemma_api_key

🧠 How It Works
The application parses natural language input using the Gemma 3 model to determine which function(s) to call:

Available Functions
find_restaurants(location: str, cuisine: str, max_price: int)

make_reservation(restaurant_name: str, guests: int)

schedule_calendar_event(summary: str, location: str, start_time: str, guests: int)

The app executes these steps in order:

Find Restaurants based on user preferences (e.g., cuisine, location, price).

Make a Reservation at the top result.

Schedule a Calendar Event for the reservation.


🛠 Tech Stack
Google Places API

Google Calendar API

Google Gemini / Gemma Models

Python, Requests, dotenv, Google API Python client



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
