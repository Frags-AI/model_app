from openai import OpenAI
from config import settings

# Initialize OpenAI client with API key from settings or use a default (which should be replaced in production)
api_key = settings.openai_key if hasattr(settings, 'openai_key') else ""
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

def generate_script_with_params(topic, tone="informative", duration=60):
    """
    Generates a script based on topic, tone, and duration using OpenAI's GPT-4.
    
    Args:
        topic (str): The main topic for the script.
        tone (str): The tone of the script (informative, entertaining, professional, etc.).
        duration (int): Target duration in seconds.
        
    Returns:
        dict: The generated script with metadata or error message.
    """
    try:
        if not api_key:
            return {"error": "OpenAI API key is not configured. Please set the OPENAI_API_KEY in your environment."}
        
        # Calculate approximate word count (average speaking rate: 150-160 words per minute)
        words_per_minute = 155
        target_words = int((duration / 60) * words_per_minute)
        
        # Create a detailed prompt based on the parameters
        prompt = f"""
Create a {tone} script for a video about "{topic}".

Requirements:
- Target duration: {duration} seconds ({duration//60} minutes {duration%60} seconds)
- Approximate word count: {target_words} words
- Tone: {tone}
- Include a compelling introduction that hooks the viewer
- Organize content with clear sections and smooth transitions
- End with a strong conclusion and call-to-action
- Make it engaging and suitable for video format
- Use natural, conversational language that's easy to speak

Format the script with clear sections and include timing guidance where appropriate.
"""
        
        # Adjust max_tokens based on duration (longer videos need more tokens)
        max_tokens = min(4000, max(500, target_words * 2))  # Cap at 4000, minimum 500
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert video script writer who creates engaging, well-structured scripts for various topics and tones."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        script_content = response.choices[0].message.content.strip()
        
        # Calculate actual word count
        actual_words = len(script_content.split())
        estimated_duration = (actual_words / words_per_minute) * 60
        
        return {
            "script": script_content,
            "metadata": {
                "topic": topic,
                "tone": tone,
                "target_duration": duration,
                "estimated_duration": round(estimated_duration, 1),
                "target_words": target_words,
                "actual_words": actual_words,
                "generated_at": "2024-01-01T00:00:00Z"  # You might want to use actual timestamp
            }
        }
    except Exception as e:
        return {"error": f"Error generating script: {str(e)}"}
