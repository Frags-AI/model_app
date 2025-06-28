import requests
import os
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration for Replicate API ---
# NOTE: You need to get an API token from Replicate (replicate.com) and set it as an environment variable.
# For example: export REPLICATE_API_TOKEN='your_token_here'
REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", None)
REPLICATE_MODEL_VERSION = "stability-ai/stable-diffusion:db21e45d3f7023abc2a46ee38a23973f6dce16bb082a930b0c49861f96d1e5BF"

def generate_image_for_prompt(prompt, output_path):
    """
    Generates an image based on a text prompt using the Replicate API.
    If no API key is found, it falls back to a placeholder image service.

    Args:
        prompt (str): The text prompt for image generation.
        output_path (str): The path to save the generated image.

    Returns:
        str: The path to the generated image, or None if generation failed.
    """
    # If no API token is available, use a placeholder image service for demonstration.
    if not REPLICATE_API_TOKEN:
        logging.warning("REPLICATE_API_TOKEN not set. Falling back to placeholder image.")
        # Sanitize prompt for URL
        safe_prompt = requests.utils.quote(prompt)
        placeholder_url = f"https://via.placeholder.com/512x512.png?text={safe_prompt}"
        try:
            response = requests.get(placeholder_url)
            response.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(response.content)
            logging.info(f"Saved placeholder image for prompt: '{prompt}'")
            return output_path
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download placeholder image: {e}")
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
