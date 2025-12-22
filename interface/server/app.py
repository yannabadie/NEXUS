from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import asyncio
import sys
import os
from pathlib import Path

# Fix Path to allow importing core
sys.path.append(str(Path(__file__).parent.parent.parent.resolve()))

# Integration with Core Generator
from core.ui.generator import ComponentGenerator

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NexusAPI")

app = FastAPI(title="NEXUS GenUI API", version="0.11.0")

# CORS for Vite Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Generator
OUTPUT_DIR = Path("interface/ui/cerebro/src/components/generated")
generator = ComponentGenerator(output_dir=str(OUTPUT_DIR))

class GenerationRequest(BaseModel):
    prompt: str

@app.get("/health")
def health_check():
    return {"status": "ok", "agent": "Claude (Async)"}

@app.post("/api/generate")
async def generate_component(request: GenerationRequest):
    """
    Trigger UI generation via Async Claude Driver.
    """
    logger.info(f"Received generation request: {request.prompt}")
    try:
        # Use the Async Generator
        file_path = await generator.generate_async(
            prompt=request.prompt, 
            component_name="GeneratedComponent", 
            use_llm=True
        )
        return {"status": "success", "file": file_path, "message": "Component generated successfully"}
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
