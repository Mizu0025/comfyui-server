import pytest
import asyncio
import json
from unittest.mock import patch, MagicMock, AsyncMock
from comfyui_client import ComfyUIClient

@patch("aiohttp.ClientSession.post")
@pytest.mark.asyncio
async def test_queue_prompt_success(mock_post):
    client = ComfyUIClient("localhost", 8188)
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"prompt_id": "test-id-123"}
    
    mock_post.return_value.__aenter__.return_value = mock_response
    
    prompt_id = await client.queue_prompt({"test": "prompt"})
    assert prompt_id == "test-id-123"

@patch("aiohttp.ClientSession.post")
@pytest.mark.asyncio
async def test_queue_prompt_failure(mock_post):
    client = ComfyUIClient("localhost", 8188)
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text.return_value = "Server Error"
    mock_post.return_value.__aenter__.return_value = mock_response
    
    with pytest.raises(Exception) as cm:
        await client.queue_prompt({"test": "prompt"})
    assert "500" in str(cm.value)

@patch("comfyui_client.websockets.connect", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_connect_websocket(mock_connect):
    client = ComfyUIClient("localhost", 8188)
    mock_ws = AsyncMock()
    mock_connect.return_value = mock_ws
    
    ws = await client.connect_websocket()
    assert ws == mock_ws
    assert client.ws == mock_ws

@pytest.mark.asyncio
async def test_get_images_from_websocket():
    client = ComfyUIClient("localhost", 8188)
    client.ws = AsyncMock()
    
    # Sequence of messages: executing node, binary image data, executing None (done)
    messages = [
        json.dumps({"type": "executing", "data": {"node": "SaveImageWebsocket", "prompt_id": "id123"}}),
        b'\x00\x00\x00\x00\x00\x00\x00\x00fake-image-data', # 8 byte header + data
        json.dumps({"type": "executing", "data": {"node": None, "prompt_id": "id123"}})
    ]
    client.ws.recv.side_effect = messages
    
    images = await client.get_images_from_websocket("id123")
    assert "SaveImageWebsocket" in images
    assert images["SaveImageWebsocket"][0] == b"fake-image-data"

@patch("aiohttp.ClientSession.post")
@pytest.mark.asyncio
async def test_unload_models(mock_post):
    client = ComfyUIClient("localhost", 8188)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_post.return_value.__aenter__.return_value = mock_response
    
    await client.unload_models()
    mock_post.assert_called_once()
    # Ensure it called /free
    assert "/free" in mock_post.call_args[0][0]
