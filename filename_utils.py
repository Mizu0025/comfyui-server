import os
import time

def get_image_filename(prompt_id: str, index: int, extension: str = "webp") -> str:
    """
    Generates a standardized filename for a generated image.
    Format: timestamp_promptId_index.extension
    """
    timestamp = int(time.time())
    return f"{timestamp}_{prompt_id}_{index}.{extension}"

def get_domain_path(filepath: str, domain: str = "") -> str:
    """
    Converts a local filesystem path to a URL path (placeholder for now).
    """
    filename = os.path.basename(filepath)
    # The original bot seems to just return the path or a URL if configured.
    # For now we'll just return the filename or relative path.
    return filename
