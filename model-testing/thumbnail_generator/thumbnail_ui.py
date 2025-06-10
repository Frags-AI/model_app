import streamlit as st
import os
from PIL import Image
from thumbnail import (
    select_best_frame, generate_thumbnail_background,
    generate_dalle3_thumbnail, generate_from_sketch,
    generate_thumbnail_overlays, add_text_and_icon
)

st.set_page_config(page_title="AI Thumbnail Creator", layout="centered")
st.title("🎮 AI Thumbnail Creator for Gaming Clips")

MODE = st.selectbox("Choose Thumbnail Mode", [
    "1. Auto Select from Video",
    "2. Prompt Only (DALL·E 3)",
    "3. Sketch + Prompt"
])

THUMB_DIR = "generated_thumbnails"
os.makedirs(THUMB_DIR, exist_ok=True)

if MODE.startswith("1"):
    uploaded_video = st.file_uploader("Upload a short video clip (.mp4)", type=["mp4", "mov"])
    if uploaded_video:
        temp_path = os.path.join(THUMB_DIR, uploaded_video.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_video.read())

        st.video(temp_path)

        if st.button("Generate Best Frame Thumbnail"):
            video_path, frame_index = select_best_frame(temp_path)
            bg_path = generate_thumbnail_background(video_path, temp_path, time_sec=frame_index / 30)
            st.image(bg_path, caption="Thumbnail Background")

            add_text = st.checkbox("Add overlay (title + icon)?")
            if add_text:
                prompt = st.text_input("Describe the thumbnail for overlay generation")
                if st.button("Generate Overlay"):
                    text_opts, icon_opts = generate_thumbnail_overlays(prompt)
                    final_path = add_text_and_icon(bg_path, text_opts, icon_opts)
                    st.image(final_path, caption="Final Thumbnail")

elif MODE.startswith("2"):
    prompt = st.text_area("Describe the thumbnail scene (DALL·E 3 prompt)")
    if st.button("Generate Thumbnail from Prompt") and prompt:
        output_path = os.path.join(THUMB_DIR, "dalle3_prompt.jpg")
        gen_path = generate_dalle3_thumbnail(prompt, output_path)
        st.image(gen_path, caption="Generated Thumbnail")

elif MODE.startswith("3"):
    uploaded_sketch = st.file_uploader("Upload sketch/image (.png or .jpg)", type=["png", "jpg", "jpeg"])
    prompt = st.text_input("Describe what should be generated")

    if uploaded_sketch and prompt:
        temp_path = os.path.join(THUMB_DIR, uploaded_sketch.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_sketch.read())

        st.image(temp_path, caption="Sketch Input")

        if st.button("Generate Thumbnail from Sketch"):
            output_path = os.path.join(THUMB_DIR, "sketch_generated.jpg")
            gen_path = generate_from_sketch(temp_path, prompt, output_path)
            st.image(gen_path, caption="Final AI Thumbnail")
