import requests
import os
import logging
import time
from PIL import Image, ImageDraw, ImageFont

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration for Replicate API ---
# NOTE: You need to get an API token from Replicate (replicate.com) and set it as an environment variable.
# For example: export REPLICATE_API_TOKEN='your_token_here'
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")
REPLICATE_MODEL_VERSION = "stability-ai/stable-diffusion:db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5BF"

def create_placeholder_image(text, width=512, height=512):
    """Generates a placeholder image locally with the given text."""
    img = Image.new('RGB', (width, height), color = (73, 109, 137))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
    d.text((10,10), text, fill=(255,255,0), font=font)
    placeholder_path = f"placeholder_{text.replace(' ', '_')[:20]}.png"
    img.save(placeholder_path)
    return placeholder_path

def generate_image_for_prompt(prompt, output_path):
    """
    Generates an image based on a text prompt using the Replicate API.
    If no API key is found, it falls back to a local placeholder image.

    Args:
        prompt (str): The text prompt for image generation.
        output_path (str): The path to save the generated image.

    Returns:
        str: The path to the generated image, or None if generation failed.
    """
    # If no API token is available, use a local placeholder image for demonstration.
    if not REPLICATE_API_TOKEN:
        logging.warning("REPLICATE_API_TOKEN not set. Falling back to local placeholder image.")
        try:
            image_path = create_placeholder_image(prompt)
            return image_path
        except Exception as e:
            logging.error(f"Failed to create local placeholder image: {e}")
            return None

    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    
    body = {
        "version": REPLICATE_MODEL_VERSION,
        "input": {"prompt": prompt},
    }

    try:
        # Start the prediction
        start_response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers=headers,
            json=body,
        )
        start_response.raise_for_status()
        prediction_data = start_response.json()
        get_url = prediction_data["urls"]["get"]

        logging.info(f"Started image generation for prompt: '{prompt}' (ID: {prediction_data['id']})")

        # Poll for the result
        while True:
            get_response = requests.get(get_url, headers=headers)
            get_response.raise_for_status()
            response_json = get_response.json()
            status = response_json["status"]

            if status == "succeeded":
                image_url = response_json["output"][0]
                break
            elif status == "failed":
                logging.error(f"Image generation failed for prompt: '{prompt}'. Error: {response_json['error']}")
                return None
            
            time.sleep(2)  # Wait before polling again

        # Download the image
        image_response = requests.get(image_url)
        image_response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(image_response.content)
        
        logging.info(f"Successfully generated and saved image to {output_path}")
        return output_path

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred with the image generation API: {e}")
        return None

if __name__ == '__main__':
    test_prompt = "a cinematic shot of a knight fighting a dragon"
    test_output = "test_image.png"
    
    print("--- Testing Image Generation ---")
    print(f"Prompt: {test_prompt}")
    print("Note: This test requires the REPLICATE_API_TOKEN environment variable.")
    print("If not set, it will generate a placeholder image instead.")

    if generate_image_for_prompt(test_prompt, test_output):
        print(f"\nImage generation successful. Image saved to {test_output}")
    else:
        print("\nFailed to generate image.")
