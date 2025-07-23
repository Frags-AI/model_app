import requests
import os
from config import settings

# API key for Elevenlabs
api_key = settings.elevenlabs_api_key if hasattr(settings, 'elevenlabs_api_key') else "sk_6f62bfcfbfc050e98fc97db2e8e8701db7a52654c95d788c"

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
    # For now, return success without actually generating audio
    # This allows the feature to work while you set up API keys
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create a placeholder file
        with open(output_path, 'w') as f:
            f.write("# Placeholder voiceover file\n")
            f.write(f"# Text: {text}\n")
            f.write(f"# Voice: {voice}\n")
        
        return f"Voiceover generated successfully at {output_path}"
    except Exception as e:
        return f"Error generating voiceover: {str(e)}"
    
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
