import requests
import os
from config import settings

# API key for Elevenlabs
api_key = settings.ELEVENLABS_API_KEY if hasattr(settings, 'ELEVENLABS_API_KEY') else "sk_6f62bfcfbfc050e98fc97db2e8e8701db7a52654c95d788c"

# Voice IDs mapping
VOICE_IDS = {
    "Jessica": "cgSgspJ2msm6clMCkdW9",
    "Adam": "pNInz6obpgDQGcFmaJgB",
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "John": "TxGEqnHWrfWFTfGW9XjX",
    "Emily": "EXAVITQu4vr4xnSDxMaL"
}

def generate_voiceover(text, voice="Jessica", output_path="voiceover.mp3"):
    """
    Generates a voiceover for the given text using Elevenlabs API.
    Args:
        text (str): Text for the voiceover.
        voice (str): Voice name.
        output_path (str): Path to save the voiceover file.
    Returns:
        str: Status of the generation.
    """
    # Get the voice ID from the mapping or use the default
    voice_id = VOICE_IDS.get(voice, "cgSgspJ2msm6clMCkdW9")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, "wb") as f:
                f.write(response.content)
            return f"Voiceover generated and saved as '{output_path}'."
        else:
            return f"Error: {response.status_code}, {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"
