import os
import logging
import asyncio
from typing import Dict, List, Optional
from PIL import Image
import io

from comfyui_client import ComfyUIClient
from prompt_processor import PromptProcessor
from workflow_loader import WorkflowLoader
from image_grid import ImageGrid
from filename_utils import get_image_filename

logger = logging.getLogger(__name__)

class ImageGenerator:
    """
    Orchestrates the entire image generation process including model configuration,
    workflow loading, ComfyUI interaction, and image saving.
    """
    def __init__(self, comfyui_address: str, comfyui_port: int, output_dir: str, model_config_path: str):
        self.comfyui_address = comfyui_address
        self.comfyui_port = comfyui_port
        self.output_dir = output_dir
        self.model_config_path = model_config_path
        self._model_configs = None

    def _load_model_configs(self):
        if self._model_configs is None:
            import json
            with open(self.model_config_path, 'r') as f:
                self._model_configs = json.load(f)
        return self._model_configs

    async def generate_image(self, filtered_prompt: Dict) -> str:
        client = ComfyUIClient(self.comfyui_address, self.comfyui_port)
        
        try:
            logger.info("Starting image generation process")
            
            # Load model configuration
            model_name = filtered_prompt.get('model')
            configs = self._load_model_configs()

            # Default model if none specified
            if not model_name or model_name not in configs or model_name == "DEFAULTS":
                model_name = configs.get("DEFAULTS", {}).get("MODEL", [k for k in configs.keys() if k != "DEFAULTS"][0])
            
            logger.info(f"Using model: {model_name}")
            model_config = configs[model_name]

            # Load workflow
            workflow_name = model_config['workflow']
            logger.info(f"Loading workflow: {workflow_name}")
            workflow_data = WorkflowLoader.load_workflow_by_name(workflow_name)
            if not workflow_data:
                raise Exception(f"Failed to load workflow: {workflow_name}")

            # Create prompt data
            prompt_wrapper = PromptProcessor.create_prompt_data(workflow_data)
            
            # Update with model config
            global_defaults = configs.get("DEFAULTS", {})
            PromptProcessor.update_prompt_with_model_config(prompt_wrapper, model_config, filtered_prompt, global_defaults)

            # Connect and queue
            await client.connect_websocket()
            prompt_id = await client.queue_prompt(prompt_wrapper['workflow'])
            if not prompt_id:
                raise Exception("Failed to queue prompt.")

            # Get images
            images_dict = await client.get_images_from_websocket(prompt_id)
            image_data_list = images_dict.get('SaveImageWebsocket', [])
            logger.info(f"Received {len(image_data_list)} image(s) from ComfyUI")

            # Save individual images
            saved_paths = await self.save_image_files(image_data_list, prompt_id)

            # Generate grid
            if len(saved_paths) > 1:
                logger.info(f"Generating image grid from {len(saved_paths)} images")
                grid_path = ImageGrid.generate_image_grid(saved_paths)
                return grid_path
            elif len(saved_paths) == 1:
                return saved_paths[0]
            else:
                raise Exception("No images were generated")

        except Exception as e:
            logger.error(f"Error during image generation: {e}")
            raise e
        finally:
            await client.close()

    async def save_image_files(self, image_data_list: List[bytes], prompt_id: str) -> List[str]:
        saved_images = []
        if not image_data_list:
            logger.warning("No images received from ComfyUI")
            return saved_images

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        for index, image_bytes in enumerate(image_data_list):
            filename = get_image_filename(prompt_id, index + 1, "webp")
            filepath = os.path.join(self.output_dir, filename)

            try:
                # Convert to webp using PIL
                img = Image.open(io.BytesIO(image_bytes))
                img.save(filepath, "WEBP")
                saved_images.append(filepath)
                logger.debug(f"Saved image: {filename}")
            except Exception as e:
                logger.error(f"Error saving image {filename}: {e}")

        return saved_images

    async def unload_models(self):
        client = ComfyUIClient(self.comfyui_address, self.comfyui_port)
        try:
            await client.unload_models()
        finally:
            await client.close()
