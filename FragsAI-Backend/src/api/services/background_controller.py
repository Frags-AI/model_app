import requests
import os
import base64
from config import settings

# API key for Stable Diffusion
api_key = settings.STABLE_DIFFUSION_API_KEY if hasattr(settings, 'STABLE_DIFFUSION_API_KEY') else ""

def generate_background(prompt, width=1920, height=1080, style="realistic", output_path="background.png"):
    """
    Generates a background image using Stable Diffusion API.
    
    Args:
        prompt (str): Text prompt for image generation.
        width (int): Width of the image.
        height (int): Height of the image.
        style (str): Style of the image (realistic, anime, etc.).
        output_path (str): Path to save the image file.
        
    Returns:
        str: Status of the generation.
    """
    if not api_key:
        return "Error: Stable Diffusion API key is not configured. Please set the STABLE_DIFFUSION_API_KEY in your environment."
    
    # API endpoint
    url = "https://stablediffusionapi.com/api/v3/text2img"
    
    # Prepare style-specific parameters
    style_params = {}
    if style.lower() == "realistic":
        style_params = {
            "sampler_name": "DPM++ 2M Karras",
            "cfg_scale": 7.5,
            "steps": 30,
        }
    elif style.lower() == "anime":
        style_params = {
            "sampler_name": "Euler a",
            "cfg_scale": 9,
            "steps": 25,
        }
    else:  # Default style
        style_params = {
            "sampler_name": "DPM++ SDE Karras",
            "cfg_scale": 7,
            "steps": 20,
        }
    
    # Prepare request payload
    payload = {
        "key": api_key,
        "prompt": prompt,
        "negative_prompt": "blurry, bad quality, distorted, deformed",
        "width": width,
        "height": height,
        **style_params
    }
    
    try:
        response = requests.post(url, json=payload)
        response_data = response.json()
        
        if response.status_code != 200:
            return f"Error: API returned status code {response.status_code}: {response_data.get('message', 'Unknown error')}"
        
        # Check if the response contains the image
        if "output" in response_data and len(response_data["output"]) > 0:
            image_url = response_data["output"][0]
            
            # Download the image
            img_response = requests.get(image_url)
            if img_response.status_code == 200:
                # Ensure directory exists
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Save the image
                with open(output_path, "wb") as f:
                    f.write(img_response.content)
                return f"Background image generated and saved as '{output_path}'."
            else:
                return f"Error downloading image: {img_response.status_code}"
        elif "base64" in response_data:
            # Some APIs return base64 encoded image
            img_data = base64.b64decode(response_data["base64"])
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save the image
            with open(output_path, "wb") as f:
                f.write(img_data)
            return f"Background image generated and saved as '{output_path}'."
        else:
            return f"Error: No image data in response: {response_data}"
    except Exception as e:
        return f"Error generating background: {str(e)}"
