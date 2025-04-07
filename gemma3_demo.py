from google import genai
import re
import io
import requests
from contextlib import redirect_stdout

# Avoid hardcoding your API key
# from google.colab import userdata
# api_key = userdata.get("API_KEY")
api_key = "AIzaSyDDeI-I7NpycfeX7CA-2k3cI0NcmwygBBI"
client = genai.Client(api_key=api_key)
model_id = "gemma-3-27b-it"

def extract_tool_call(text):
    pattern = r"
tool_code\s*(.*?)\s*
"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        code = match.group(1).strip()
        f = io.StringIO()
        with redirect_stdout(f):
            try:
                result = eval(code)
                output = f.getvalue()
                return f'
tool_output\n{output or result}\n
'
            except Exception as e:
                return f"Error in tool execution: {e}"
    return None

def get_exchange_rate(currency, new_currency):
    url = f"https://api.exchangerate-api.com/v4/latest/{currency}"
    response = requests.get(url)
    data = response.json()
    return data["rates"].get(new_currency, None)

def convert(amount, currency, new_currency):
    rate = get_exchange_rate(currency, new_currency)
    if rate is None:
        raise ValueError(f"Exchange rate not found for {currency} to {new_currency}")
    return amount * rate

instruction_prompt_with_function_calling = '''At each turn, if you decide to invoke any of the function(s), it should be wrapped with 
tool_code
. The Python methods available:

python
def convert(amount, currency, new_currency):
    """Convert the currency with the latest exchange rate"""

def get_exchange_rate(currency, new_currency):
    """Get the latest exchange rate for the currency pair"""

    User: {user_message}'''

chat = client.chats.create(model=model_id)

user_message = "Convert 100 USD to INR"
response = chat.send_message(instruction_prompt_with_function_calling.format(user_message=user_message))

print("Model Response:\n", response.text)

tool_result = extract_tool_call(response.text)
if tool_result: print("\nTool Execution Result:\n", tool_result)

response = chat.send_message(tool_result)
print(response.text)