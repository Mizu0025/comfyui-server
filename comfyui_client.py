import asyncio
import json
import uuid
import logging
import aiohttp
import websockets
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class ComfyUIClient:
    """
    A client for interacting with the ComfyUI API and WebSocket server.
    Handles prompt queueing, model unloading, and real-time image retrieval.
    """
    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port
        self.client_id = str(uuid.uuid4())
        self.ws = None
        logger.debug(f"Created ComfyUI client with ID: {self.client_id}")

    async def queue_prompt(self, prompt: Dict) -> Optional[str]:
        """
        Queues a prompt to the ComfyUI server for processing.
        """
        url = f"http://{self.address}:{self.port}/prompt"
        payload = {"prompt": prompt, "client_id": self.client_id}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"ComfyUI Error ({response.status}): {error_text}")
                        raise Exception(f"HTTP error! status: {response.status}, message: {error_text}")
                    
                    result = await response.json()
                    logger.info(f"Prompt queued successfully with ID: {result['prompt_id']}")
                    return result['prompt_id']
        except Exception as e:
            logger.error(f"Error queuing prompt: {e}")
            raise Exception(f"Failed to queue prompt: {e}")

    async def connect_websocket(self):
        """
        Connects to the ComfyUI WebSocket server for real-time updates.
        """
        uri = f"ws://{self.address}:{self.port}/ws?clientId={self.client_id}"
        try:
            self.ws = await websockets.connect(uri, max_size=None)
            logger.info(f"Connected to ComfyUI WebSocket at {self.address}")
            return self.ws
        except Exception as e:
            logger.error(f"Error connecting to ComfyUI server: {e}")
            raise Exception(f"Could not connect to ComfyUI server at {self.address}. Is the server running?")

    async def get_images_from_websocket(self, prompt_id: str) -> Dict[str, List[bytes]]:
        """
        Monitors the WebSocket for status updates and binary image data.
        """
        if not self.ws:
            raise Exception("WebSocket not connected")

        output_images = {}
        current_node = ""
        logger.debug(f"Waiting for images from prompt ID: {prompt_id}")

        try:
            while True:
                message = await self.ws.recv()
                
                if isinstance(message, str):
                    # JSON message
                    data = json.loads(message)
                    logger.debug(f"Received WebSocket message type: {data['type']}")

                    if data['type'] == 'executing':
                        executing_data = data['data']
                        if executing_data['prompt_id'] == prompt_id:
                            if executing_data['node'] is None:
                                # Execution is done
                                image_count = len(output_images.get('SaveImageWebsocket', []))
                                logger.info(f"Execution complete. Received {image_count} image(s) for prompt {prompt_id}")
                                return output_images
                            else:
                                logger.info(f"Executing node: {executing_data['node']} (prompt: {prompt_id})")
                                current_node = executing_data['node']
                else:
                    # Binary data (image)
                    if current_node == 'SaveImageWebsocket':
                        if current_node not in output_images:
                            output_images[current_node] = []
                        
                        # Remove the first 8 bytes (header) and add the image data
                        image_data = message[8:]
                        logger.debug(f"Received binary image data: {len(image_data)} bytes")
                        output_images[current_node].append(image_data)
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
            raise Exception(f"Error processing WebSocket message: {e}")

    async def close(self):
        """
        Closes the active WebSocket connection.
        """
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def unload_models(self):
        """
        Sends a request to the server's /free endpoint to unload models and free VRAM.
        """
        url = f"http://{self.address}:{self.port}/free"
        payload = {
            "unload_models": True,
            "free_memory": True
        }
        
        try:
            logger.info("Requesting ComfyUI to unload models...")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"ComfyUI Unload Models Error ({response.status}): {error_text}")
                    else:
                        logger.info("Successfully requested model unloading.")
        except Exception as e:
            logger.error(f"Error requesting model unloading: {e}")
