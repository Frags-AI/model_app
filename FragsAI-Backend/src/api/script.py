from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .services import script_controller

router = APIRouter()

class ScriptRequest(BaseModel):
    topic: str
    tone: str = "informative"
    duration: int = 60

@router.post("/generate/")
async def generate_script(request: ScriptRequest):
    """
    Generate a script based on topic, tone, and duration using OpenAI's GPT-4
    """
    try:
        result = script_controller.generate_script_with_params(
            topic=request.topic,
            tone=request.tone,
            duration=request.duration
        )
        
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return JSONResponse({
            "message": "Script generated successfully",
            "script": result["script"],
            "metadata": result.get("metadata", {}),
            "status": "success"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-legacy/")
async def generate_script_legacy(prompt: str = Form(...)):
    """
    Generate a script based on a prompt using OpenAI's GPT-4 (legacy endpoint)
    """
    result = script_controller.generate_script(prompt)
    
    if "error" in result.lower():
        return JSONResponse({"error": result}, status_code=400)
    
    return JSONResponse({
        "message": "Script generated successfully",
        "script": result,
        "status": "success"
    })

@router.post("/generate-stream/")
async def generate_stream_script(prompt: str = Form(...)):
    """
    Generate a title and script for a streaming video based on a prompt
    """
    result = script_controller.generate_stream_script(prompt)
    
    if "error" in result.lower():
        return JSONResponse({"error": result}, status_code=400)
    
    # Parse the result to separate title and script
    parts = result.split("\n\n", 1)
    title = parts[0].replace("Title: ", "") if len(parts) > 0 else ""
    script = parts[1] if len(parts) > 1 else result
    
    return JSONResponse({
        "message": "Stream script generated successfully",
        "title": title,
        "script": script,
        "status": "success"
    })
