import pytest
import os
from unittest.mock import patch, MagicMock
from image_grid import ImageGrid

@patch("image_grid.Image.open")
@patch("image_grid.Image.new")
def test_generate_image_grid_multiple(mock_new, mock_open):
    # Setup mocks
    mock_img = MagicMock()
    mock_img.size = (100, 100)
    mock_open.return_value = mock_img
    
    mock_grid = MagicMock()
    mock_new.return_value = mock_grid
    
    image_paths = ["img1.webp", "img2.webp", "img3.webp", "img4.webp"]
    output = ImageGrid.generate_image_grid(image_paths, "grid.webp")
    
    # Check grid dimensions for 4 images (should be 2x2)
    mock_new.assert_called_with('RGB', (200, 200))
    assert mock_grid.paste.call_count == 4
    mock_grid.save.assert_called_with("grid.webp", "WEBP")
    assert output == "grid.webp"

@patch("image_grid.Image.open")
def test_generate_image_grid_single(mock_open):
    image_paths = ["img1.webp"]
    output = ImageGrid.generate_image_grid(image_paths)
    assert output == "img1.webp"

def test_generate_image_grid_empty():
    with pytest.raises(ValueError):
        ImageGrid.generate_image_grid([])

@patch("image_grid.Image.open")
@patch("image_grid.Image.new")
def test_generate_image_grid_auto_path(mock_new, mock_open):
    mock_img = MagicMock()
    mock_img.size = (100, 100)
    mock_open.return_value = mock_img
    mock_new.return_value = MagicMock()
    
    image_paths = ["/path/to/img1.webp", "/path/to/img2.webp"]
    output = ImageGrid.generate_image_grid(image_paths)
    
    assert output.endswith("img1_grid.webp")
    assert os.path.dirname(output) == "/path/to"
