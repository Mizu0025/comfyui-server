import pytest
import os
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from image_generator import ImageGenerator

@patch("image_generator.ImageGenerator._load_model_configs")
@patch("image_generator.WorkflowLoader.load_workflow_by_name")
@patch("image_generator.ComfyUIClient")
@patch("image_generator.ImageGenerator.save_image_files")
@pytest.mark.asyncio
async def test_generate_image_success(mock_save, mock_client_class, mock_load_wf, mock_load_configs):
    generator = ImageGenerator(
        "localhost", 8188, "/tmp/output", "config/modelConfiguration.json"
    )
    mock_configs = {
        "model1": {"workflow": "wf1", "checkpointName": "ckpt1"},
        "DEFAULTS": {"MODEL": "model1"}
    }
    # Setup mocks
    mock_load_configs.return_value = mock_configs
    mock_load_wf.return_value = {"Checkpoint": {"inputs": {}}}
    
    mock_client = mock_client_class.return_value
    mock_client.connect_websocket = AsyncMock()
    mock_client.queue_prompt = AsyncMock(return_value="prompt-123")
    mock_client.get_images_from_websocket = AsyncMock(return_value={"SaveImageWebsocket": [b"data"]})
    mock_client.close = AsyncMock()
    
    mock_save.return_value = ["/tmp/output/img1.webp"]
    
    result = await generator.generate_image({"model": "model1", "prompt": "test"})
    
    assert result == "/tmp/output/img1.webp"
    mock_client.queue_prompt.assert_called_once()
    mock_save.assert_called_once()

@patch("os.path.exists", return_value=True)
@patch("image_generator.Image.open")
@pytest.mark.asyncio
async def test_save_image_files(mock_image_open, mock_exists):
    generator = ImageGenerator(
        "localhost", 8188, "/tmp/output", "config/modelConfiguration.json"
    )
    mock_img = MagicMock()
    mock_image_open.return_value = mock_img
    
    image_data = [b"fake-data-1", b"fake-data-2"]
    paths = await generator.save_image_files(image_data, "prompt123")
    
    assert len(paths) == 2
    assert paths[0].endswith(".webp")
    assert mock_img.save.call_count == 2

@patch("image_generator.ComfyUIClient")
@pytest.mark.asyncio
async def test_unload_models(mock_client_class):
    generator = ImageGenerator("localhost", 8188, "/tmp/output", "config/modelConfiguration.json")
    mock_client = mock_client_class.return_value
    mock_client.unload_models = AsyncMock()
    mock_client.close = AsyncMock()
    
    await generator.unload_models()
    
    mock_client.unload_models.assert_called_once()
    mock_client.close.assert_called_once()
