import pytest
import base64
import os
from pathlib import Path
from unittest.mock import patch

from compass.tools.computer import ComputerTool, ToolError
from compass.tools.base import ToolResult

@pytest.fixture
def computer_tool():
    """Setup computer tool with mock display dimensions"""
    os.environ["WIDTH"] = "1920"
    os.environ["HEIGHT"] = "1080"
    return ComputerTool()

@pytest.mark.asyncio
async def test_screenshot_capture(computer_tool):
    """Test basic screenshot functionality"""
    result = await computer_tool(action="screenshot")
    
    assert result.error is None  # Error should be None on success
    assert result.output is None  # Output should be None because screencapture is silent
    assert result.base64_image is not None  # Screenshot data should be present
    assert isinstance(result.base64_image, str)  # Should be base64 string
    
    # Updated path to be relative to backend directory
    output_dir = Path(__file__).parent.parent / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    image_data = base64.b64decode(result.base64_image)
    output_path = output_dir / "test_screenshot.png"
    
    with open(output_path, "wb") as f:
        f.write(image_data)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

@pytest.mark.asyncio
async def test_invalid_action(computer_tool):
    """Test handling of invalid actions"""
    with pytest.raises(Exception) as exc_info:
        await computer_tool(action="invalid_action")
    
    assert "Action 'invalid_action' is not implemented yet" in str(exc_info.value)

@pytest.mark.asyncio
async def test_missing_dimensions():
    """Test handling of missing display dimensions"""
    os.environ.pop("WIDTH", None)
    os.environ.pop("HEIGHT", None)
    
    with pytest.raises(AssertionError) as exc_info:
        ComputerTool()
    
    assert "WIDTH and HEIGHT must be set" in str(exc_info.value) 

@pytest.mark.asyncio
async def test_left_click_command_verification(computer_tool):
    """Test that left click generates correct cliclick command"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        # Configure mock to return empty ToolResult
        mock_shell.return_value = ToolResult(output=None, error=None)
        
        # Test valid left click
        await computer_tool(action="left_click", coordinate=(100, 200))
        mock_shell.assert_called_once_with("cliclick c:100,200")

@pytest.mark.asyncio
async def test_right_click_command_verification(computer_tool):
    """Test that right click generates correct cliclick command"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        mock_shell.return_value = ToolResult(output=None, error=None)
        
        # Test valid right click
        await computer_tool(action="right_click", coordinate=(150, 300))
        mock_shell.assert_called_once_with("cliclick rc:150,300")

@pytest.mark.asyncio
async def test_click_coordinate_validation(computer_tool):
    """Test various invalid click coordinates"""
    test_cases = [
        # Missing coordinates
        (None, "coordinate is required for left_click"),
        # Invalid tuple length
        ((100,), "must be a tuple of length 2"),
        # Negative coordinates
        ((-10, 100), "must be a tuple of non-negative ints"),
        # Out of bounds coordinates
        ((2000, 2000), "are out of bounds"),
        # Wrong type
        (("100", "200"), "must be a tuple of non-negative ints"),
    ]
    
    for coordinate, expected_error in test_cases:
        with pytest.raises(ToolError) as exc_info:
            await computer_tool(action="left_click", coordinate=coordinate)
        assert expected_error in str(exc_info.value)

@pytest.mark.asyncio
async def test_click_edge_cases(computer_tool):
    """Test edge cases for click coordinates"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        mock_shell.return_value = ToolResult(output=None, error=None)
        
        # Test clicking at (0, 0)
        await computer_tool(action="left_click", coordinate=(0, 0))
        mock_shell.assert_called_with("cliclick c:0,0")
        
        # Test clicking at maximum bounds
        max_x, max_y = computer_tool.width, computer_tool.height
        await computer_tool(action="right_click", coordinate=(max_x, max_y))
        mock_shell.assert_called_with(f"cliclick rc:{max_x},{max_y}")

@pytest.mark.asyncio
async def test_click_shell_error_propagation(computer_tool):
    """Test that shell errors are properly propagated"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        # Simulate shell command error
        mock_shell.return_value = ToolResult(error="Command failed")
        
        result = await computer_tool(action="left_click", coordinate=(100, 100))
        assert result.error == "Command failed" 