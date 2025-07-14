from openai import OpenAI
from config import settings

# Initialize OpenAI client with API key from settings or use a default (which should be replaced in production)
api_key = settings.OPENAI_API_KEY if hasattr(settings, 'OPENAI_API_KEY') else ""
client = OpenAI(api_key=api_key)

def generate_script(prompt):
    """
    Generates a script based on the provided prompt using OpenAI's GPT-4.
    
    Args:
        prompt (str): The prompt for script generation.
        
    Returns:
        str: The generated script or error message.
    """
    try:
        if not api_key:
            return "Error: OpenAI API key is not configured. Please set the OPENAI_API_KEY in your environment."
        
        response = client.chat.completions.create(
            model="gpt-4",  # or your preferred model
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating script: {str(e)}"

def generate_stream_script(prompt):
    """
    Generates a title and script for a streaming video based on the provided prompt.
    
    Args:
        prompt (str): The prompt for script generation.
        
    Returns:
        str: The generated title and script or error message.
    """
    try:
        if not api_key:
            return "Error: OpenAI API key is not configured. Please set the OPENAI_API_KEY in your environment."
        
        # Generate title
        title_prompt = f"Generate a catchy and engaging title for a YouTube video about: {prompt}"
        title_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": title_prompt}
            ],
            max_tokens=50,
            temperature=0.7
        )
        title = title_response.choices[0].message.content.strip()
        
        # Generate script
        script_prompt = f"Write a compelling script for a YouTube video with the title: {title}. The video is about: {prompt}. Include an engaging introduction, main points, and a call to action at the end."
        script_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": script_prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        script = script_response.choices[0].message.content.strip()
        
        return f"Title: {title}\n\nScript:\n{script}"
    except Exception as e:
        return f"Error generating stream script: {str(e)}"
