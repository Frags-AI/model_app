from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse, FileResponse
from .services import background_controller
import os
import uuid

router = APIRouter()

@router.post("/generate/")
async def generate_background(
    prompt: str = Form(...),
    width: int = Form(1920),
    height: int = Form(1080),
    style: str = Form("realistic")
):
    """
    Generate a background image using Stable Diffusion API
    """
    # Create a unique filename for the output
    output_filename = f"background_{uuid.uuid4()}.png"
    output_path = os.path.join("./uploads/backgrounds", output_filename)
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Generate the background image
    result = background_controller.generate_background(prompt, width, height, style, output_path)
    
    if "error" in result.lower():
        return JSONResponse({"error": result}, status_code=400)
    
    # Return the file path and a success message
    return JSONResponse({
        "message": "Background image generated successfully",
        "file_path": output_path,
        "filename": output_filename,
        "status": "success"
    })

@router.get("/download/{filename}")
async def download_background(filename: str):
    """
    Download a generated background image
    """
    file_path = os.path.join("./uploads/backgrounds", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png", filename=filename)
    else:
        return JSONResponse({"error": "File not found"}, status_code=404)
