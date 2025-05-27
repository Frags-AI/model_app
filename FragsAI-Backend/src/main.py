from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from config import settings
from api.router import router as api_router
from websocket.router import router as ws_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
      "https://fragsai.com", 
      "https://www.fragsai.com", 
      "https://www.model.fragsai.com", 
      "https://model.fragsai.com", 
      "https://www.backend.fragsai.com",
      "https://backend.fragsai.com",
      "http://localhost:5173.com",
      "http://localhost:8000.com",
      "http://localhost:3000.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(api_router, prefix="/api")
app.include_router(ws_router, prefix="/ws")

@app.get("/")
async def server_status():
    return JSONResponse({"message": "LLM server is active and running"})

if __name__ == "__main__" and settings.environment == "DEVELOPMENT":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)