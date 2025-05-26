import cv2
import numpy as np
import ast
import json
import requests
from .virality_ranking import predict_actions
from config import settings
import logging

# Initialize OpenAI client
import openai
openai.api_key=settings.openai_key

cv2_map = {
    "cv2.FONT_HERSHEY_SIMPLEX": cv2.FONT_HERSHEY_SIMPLEX,
    "cv2.FONT_HERSHEY_PLAIN": cv2.FONT_HERSHEY_PLAIN,
    "cv2.FONT_HERSHEY_DUPLEX": cv2.FONT_HERSHEY_DUPLEX,
    "cv2.FONT_HERSHEY_COMPLEX": cv2.FONT_HERSHEY_COMPLEX,
    "cv2.FONT_HERSHEY_TRIPLEX": cv2.FONT_HERSHEY_TRIPLEX,
    "cv2.FONT_HERSHEY_COMPLEX_SMALL": cv2.FONT_HERSHEY_COMPLEX_SMALL,
    "cv2.FONT_HERSHEY_SCRIPT_SIMPLEX": cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
    "cv2.FONT_HERSHEY_SCRIPT_COMPLEX": cv2.FONT_HERSHEY_SCRIPT_COMPLEX,
    "cv2.FONT_ITALIC": cv2.FONT_ITALIC
}

# -------- Mode 1: Best Frame from Clip -------- #
def select_best_frame(video_path: str):
    predictions = predict_actions(video_path)
    frame_confidences = np.max(np.array(predictions))
    best_index = np.argmax(frame_confidences)
    return video_path, best_index

def generate_thumbnail_background(video_path: str, output_path: str, time_sec=7, size: tuple[int, int] = (1280, 720)):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000)
    success, frame = cap.read()
    cap.release()
    if success:
        thumbnail = cv2.resize(frame, size)
        path = output_path.replace('.jpg', '_background.jpg')
        cv2.imwrite(path, thumbnail)
        return path, size
    return None

# -------- Mode 2: Prompt-Based DALL·E 3 -------- #
def generate_dalle3_thumbnail(prompt, output_path="thumbnail_dalle3.jpg"):
    response = openai.images.generate(  # ✅ was `client.images.generate`
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )

    image_url = response.data[0].url
    image_data = requests.get(image_url).content
    with open(output_path, "wb") as f:
        f.write(image_data)
    return output_path

# -------- Mode 3: Sketch + Prompt -------- #
def generate_from_sketch(sketch_path: str, prompt: str, output_path: str):

    image = open(sketch_path, "rb")

    response = openai.images.edit(  # ✅ change `.generate` to `.edit`
        image=image,
        prompt=prompt,
        size="1024x1024",
        n=1
    )

    image_url = response.data[0].url
    image_data = requests.get(image_url).content
    
    with open(output_path, "wb") as f:
        f.write(image_data)
    return output_path

# -------- Text + Icon Overlays -------- #
def add_text_and_icon(image_path: str, text_options: dict = None, icon_options: dict = None):
    image = cv2.imread(image_path)
    if image is None:
        return None
    if text_options:
        text = text_options.get("text", "Viral Gaming Moment")
        font = text_options.get("font", cv2.FONT_HERSHEY_SIMPLEX)
        font = cv2_map[font] if str == type(font) else cv2.FONT_HERSHEY_SIMPLEX
        scale = text_options.get("font_scale", 2)
        thickness = text_options.get("font_thickness", 5)
        color = ast.literal_eval(text_options['text_color']) if text_options.get('text_color') else (255, 255, 255)
        shadow = ast.literal_eval(text_options['shadow_color']) if text_options.get('shadow_color') else (0, 0, 0)
        pos = text_options["position"]
        x, y = pos['x'], pos['y']
        cv2.putText(image, text, (x + 2, y + 2), font, scale, shadow, thickness + 2, cv2.LINE_AA)
        cv2.putText(image, text, (x, y), font, scale, color, thickness, cv2.LINE_AA)

    if icon_options:
        icon = icon_options.get("icon_type", "play")
        size = int(icon_options.get("size", 100))
        pos = icon_options["position"]
        cx, cy = pos['x'], pos['y']
        color = ast.literal_eval(icon_options['color']) if icon_options.get('color') else (0, 255, 0)

        if icon == "play":
            pts = np.array([
                (cx - size // 2, cy - size // 2),
                (cx - size // 2, cy + size // 2),
                (cx + size // 2, cy)
            ], np.int32)
            cv2.fillPoly(image, [cv2.convexHull(pts)], color)
        elif icon == "circle":
            cv2.circle(image, (cx, cy), size // 2, color, -1)
        elif icon == "square":
            cv2.rectangle(image, (cx - size // 2, cy - size // 2), (cx + size // 2, cy + size // 2), color, -1)

    output_final = image_path.replace("_background", "")
    cv2.imwrite(output_final, image)
    return output_final

# -------- GPT Assist (Text/Icon Generator) -------- #
def generate_thumbnail_overlays(text: str, size: tuple[int, int]):
    gpt_prompt = (
        f"You're generating overlay options for a {size[0]}x{size[1]} thumbnail image.\n\n"
        f"Return a JSON object with:\n"
        f"- `text_options`: includes \"text\" (equal to this output: {text}), font (use cv2 constant), "
        f"font_scale, font_thickness, text_color (RGB as string), shadow_color (RGB), and position (x, y).\n"
        f"- `icon_options`: includes \"icon_type\" (play, circle, or square), size, color (RGB as string), "
        f"and position (x, y).\n\n"
        "Make sure the text and icon do not overlap and are positioned clearly within the frame. The text and icon should also be large to fit the screen and be centered with the icon positioned below the text"
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that generates thumbnail overlay options. "
                        "Respond strictly in JSON format with two keys: `text_options` and `icon_options`. "
                        "Example: {"
                        "'text_options': {'text': 'This is an overlay', 'font': 'cv2.FONT_HERSHEY_SIMPLEX', "
                        "'font_scale': 1, 'font_thickness': 2, 'text_color': '(255, 255, 255)', "
                        "'shadow_color': '(0, 0, 0)', 'position': {'x': 100, 'y': 200}}, "
                        "'icon_options': {'icon_type': 'play', 'size': 60, 'color': '(0, 255, 0)', "
                        "'position': {'x': 1100, 'y': 600}}}"
                    )
                },
                { "role": "user", "content": gpt_prompt }
            ],
            temperature=0.7,
            max_tokens=300
        )

        content = response.choices[0].message.content.strip()
        options: dict = json.loads(content)
        print(options["text_options"])
        return options.get("text_options"), options.get("icon_options")

    except json.JSONDecodeError:
        logging.error("Invalid JSON returned by GPT:\n%s", content)
    except Exception as e:
        logging.error("Failed to get response from OpenAI: %s", str(e))

    return None, None