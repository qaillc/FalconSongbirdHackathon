from ai71 import AI71
from config import get_ai71_api_key

AI71_API_KEY = get_ai71_api_key()

"""
def generate_response(system_message, user_message):
    response_text = ""
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
        model="tiiuae/falcon-180b-chat",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        stream=True,
    ):
        if chunk.choices[0].delta.content:
            response_text += chunk.choices[0].delta.content
    return response_text

"""

def generate_response(system_message, user_message):
    response_text = ""
    for chunk in AI71(AI71_API_KEY).chat.completions.create(
        model="tiiuae/falcon-180b-chat",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        stream=True,
    ):
        if chunk.choices[0].delta.content:
            response_text += chunk.choices[0].delta.content
    
    # Ensure no extra characters or unfinished text is appended
    response_text = response_text.rstrip()
    
    return response_text

