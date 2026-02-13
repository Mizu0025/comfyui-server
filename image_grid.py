import math
import logging
from PIL import Image
from typing import List
import os

logger = logging.getLogger(__name__)

class ImageGrid:
    """
    Handles the creation of a tiled grid from multiple individual images.
    """
    @staticmethod
    async def generate_image_grid(image_paths: List[str], output_path: str = None) -> str:
        """
        Creates a vertical or square grid from individual images.
        """
        if not image_paths:
            raise ValueError("No images provided for grid generation")

        import asyncio

        def _create_grid():
            images = [Image.open(p) for p in image_paths]
            count = len(images)
            
            if count == 1:
                return image_paths[0]

            # Calculate grid dimensions
            cols = math.ceil(math.sqrt(count))
            rows = math.ceil(count / cols)

            # Assume all images are the same size as the first one
            width, height = images[0].size
            
            grid_width = cols * width
            grid_height = rows * height
            
            grid_image = Image.new('RGB', (grid_width, grid_height))
            
            for i, img in enumerate(images):
                x = (i % cols) * width
                y = (i // cols) * height
                grid_image.paste(img, (x, y))
            
            target_path = output_path
            if not target_path:
                # Generate a grid filename based on the first image path
                dir_name = os.path.dirname(image_paths[0])
                base_name = os.path.basename(image_paths[0])
                name, ext = os.path.splitext(base_name)
                target_path = os.path.join(dir_name, f"{name}_grid{ext}")

            grid_image.save(target_path, "WEBP")
            return target_path

        result_path = await asyncio.to_thread(_create_grid)
        logger.info(f"Image grid saved to: {result_path}")
        return result_path
