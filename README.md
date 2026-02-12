# FateBot Image Generation Service

A high-performance, FastAPI-powered microservice designed to interface with **ComfyUI** for orchestrated image generation. This service manages a job queue, processes complex prompt modifiers, and features intelligent VRAM management for multi-user environments (like IRC or Matrix bots).

## ✨ Features

- **🚀 FastAPI Backend**: Asynchronous, high-throughput API for handling generation requests.
- **🧵 Job Queue System**: Sequential processing of generation tasks with status tracking and blocked waiting.
- **🎨 Dynamic Workflows**: Orchestrates ComfyUI workflows dynamically. Includes templates for **SDXL** and **Lumina** architectures.
- **🔍 Smart Prompt Parsing**: Supports natural language prompts mixed with CLI-style modifiers (e.g., `--model`, `--width`, `--count`).
- **🧠 VRAM Management**: Automatically unloads models from the GPU after a period of inactivity (default 10 minutes) to save resources.
- **🖼️ Image Post-Processing**: Automatically generates image grids for multi-image requests, saving the final output in optimized **WebP** format.
- **⚙️ Deeply Configurable**: Fine-tune defaults, model-specific checkpoints, and workflow mappings via JSON.

## 🏗️ Architecture

The service acts as a bridge between a frontend client (like an IRC or Matrix bot) and a ComfyUI backend:

1.  **Client** sends a POST request with a prompt and user metadata.
2.  **Service** parses the prompt, extracts modifiers, and adds the task to the internal `asyncio.Queue`.
3.  **Worker** processes the queue, maps the request to a specific ComfyUI workflow, and communicates with ComfyUI via WebSocket/REST.
4.  **ComfyUI** generates the image(s).
5.  **Service** retrieves, processes (grids if needed), and saves the local output, then resolves the job.

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A running instance of **ComfyUI** with accessible API ports.

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/ImageGen-Server.git
    cd ImageGen-Server
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    # venv\Scripts\activate   # On Windows
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure environment**:
    Create a `.env` file in the root directory:
    ```env
    COMFYUI_ADDRESS=127.0.0.1
    COMFYUI_PORT=8188
    COMFYUI_FOLDER_PATH=/path/to/comfyui/output
    LOG_LEVEL=INFO
    ```

4.  **Run the service**:
    (Ensure the virtual environment is activated)
    ```bash
    uvicorn app:app --host 0.0.0.0 --port 8000
    ```

## ⚙️ Configuration

### Model Configuration (`config/modelConfiguration.json`)

Define your models, default prompts, and workflow mappings here. Each key represents a model ID that can be targeted via the `--model` flag.

| Key | Description |
| :--- | :--- |
| `checkpointName` | The `.safetensors` file to load in ComfyUI. |
| `workflow` | The template name in the `workflows/` directory. |
| `steps` | Default sampling steps. |
| `imageWidth`/`Height` | Resolution for this specific model. |
| `defaultPositivePrompt` | Suffix/Prefix added to every prompt for this model. |
| `DEFAULTS` | Global fallbacks for width, height, count, and model. |

## ⌨️ Prompt Syntax

The service parses user messages into structured generation data. Anything before the first modifier is treated as the primary prompt.

### Supported Modifiers

| Flag | Short | Description | Example |
| :--- | :--- | :--- | :--- |
| `--model` | `-m` | Select a specific model config | `--model illustriousXL` |
| `--width` | `-w` | Set custom width | `--width 1024` |
| `--height` | `-h` | Set custom height | `--height 1280` |
| `--no` | `-n` | Add negative prompt elements | `--no blurry, text` |
| `--count` | `-c` | Number of images to generate (1-4) | `--count 4` |
| `--seed` | `-s` | Fix the random seed | `--seed 12345` |

**Example Usage**:
`A beautiful sunset over a cyberpunk city -m paSanctuary -w 1280 -h 720 -c 4`

## 📡 API Endpoints

### `POST /request`
Submit a new generation task.
- **Body**: `{"message": "prompt string", "nick": "username"}`
- **Response**: `{"job_id": "uuid", "queue_position": 1}`

### `GET /job/{job_id}`
Check current status of a task.
- **Response**: `{"status": "queued/processing/completed/failed", "result": "path_to_image", "error": null}`

### `GET /wait/{job_id}`
Block until the job finishes and return the final result.

### `GET /models`
Lists all available models defined in `modelConfiguration.json`.

---

### 📘 Interactive Documentation

FastAPI automatically provides interactive documentation for this service:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs) (Interactive testing)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc) (Clean, structured view)

---

Developed with ❤️ for the FateBot Ecosystem.
