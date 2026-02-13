import os
import logging
import asyncio
import uuid
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from image_generator import ImageGenerator
from prompt_parser import PromptParser
from filename_utils import get_domain_path

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: Start multiple workers to handle concurrency
    for i in range(MAX_CONCURRENT_JOBS):
        logger.info(f"Starting worker {i+1}/{MAX_CONCURRENT_JOBS}")
        asyncio.create_task(worker())
    
    reset_inactivity_timer()
    yield
    # Shutdown logic can go here if needed

app = FastAPI(title="FateBot Image Generation Service", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
COMFYUI_ADDRESS = os.getenv("COMFYUI_ADDRESS", "127.0.0.1")
COMFYUI_PORT = int(os.getenv("COMFYUI_PORT", 8188))
COMFYUI_FOLDER_PATH = os.getenv("COMFYUI_FOLDER_PATH", "./output")
WEB_DOMAIN = os.getenv("WEB_DOMAIN", "")
MODEL_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "modelConfiguration.json")
# Generation Service
generator = ImageGenerator(
    comfyui_address=COMFYUI_ADDRESS,
    comfyui_port=COMFYUI_PORT,
    output_dir=COMFYUI_FOLDER_PATH,
    model_config_path=MODEL_CONFIG_PATH
)

# Concurrency setting (Default to 1 for strict FIFO)
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "1"))

# Task Queue System
class Job:
    def __init__(self, raw_message: str, nick: str):
        self.id = str(uuid.uuid4())
        self.raw_message = raw_message
        self.nick = nick
        self.status = "queued"
        self.result = None
        self.error = None
        self.event = asyncio.Event()

queue = asyncio.Queue()
jobs: Dict[str, Job] = {}
active_jobs: Dict[str, Job] = {}

# Inactivity Management
inactivity_timer: Optional[asyncio.TimerHandle] = None
INACTIVITY_DELAY = 10 * 60  # 10 minutes

def reset_inactivity_timer():
    global inactivity_timer
    if inactivity_timer:
        inactivity_timer.cancel()
    inactivity_timer = asyncio.get_event_loop().call_later(INACTIVITY_DELAY, lambda: asyncio.create_task(unload_vram_task()))

async def unload_vram_task():
    if active_jobs or not queue.empty():
        logger.info("Skipping VRAM unload: Jobs are still active or queued.")
        reset_inactivity_timer()
        return

    logger.info("Inactivity detected. Unloading VRAM.")
    try:
        await generator.unload_models()
    except Exception as e:
        logger.error(f"Auto-unload failed: {e}")

# Worker Loop
async def worker():
    while True:
        job = await queue.get()
        active_jobs[job.id] = job
        job.status = "processing"
        logger.info(f"Processing job {job.id} for {job.nick}")
        
        try:
            # Parse prompt
            raw_msg = job.raw_message
            try:
                filtered_prompt = PromptParser.parse_input(raw_msg)
            except Exception as pe:
                raise Exception(f"[Prompt Error] Failed to parse options: {pe}")
            
            # Generate
            image_path = await generator.generate_image(filtered_prompt)
            job.result = get_domain_path(image_path, WEB_DOMAIN) if WEB_DOMAIN else image_path
            
            job.status = "completed"
            logger.info(f"Job {job.id} completed for {job.nick}")
        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")
            job.error = str(e)
            job.status = "failed"
        finally:
            active_jobs.pop(job.id, None)
            job.event.set()
            queue.task_done()
            reset_inactivity_timer()



# API Endpoints
class GenerateRequest(BaseModel):
    message: str
    nick: str

class GenerateResponse(BaseModel):
    job_id: str
    queue_position: int

@app.post("/request", response_model=GenerateResponse)
async def request_generation(request: GenerateRequest):
    reset_inactivity_timer()
    job = Job(request.message, request.nick)
    jobs[job.id] = job
    await queue.put(job)
    
    # Position calculation: everything in queue + anything currently running
    pos = queue.qsize() + len(active_jobs)
        
    return GenerateResponse(job_id=job.id, queue_position=pos)

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return {
        "status": job.status,
        "result": job.result,
        "error": job.error
    }

@app.get("/wait/{job_id}")
async def wait_for_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    await job.event.wait()
    return {
        "status": job.status,
        "result": job.result,
        "error": job.error
    }

@app.get("/models")
async def list_models():
    configs = generator._load_model_configs()
    models = [k for k in configs.keys() if k != "DEFAULTS"]
    return {"models": models}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
