import pytest
import base64
import os
from pathlib import Path
from unittest.mock import patch
from unittest.mock import call

from compass.tools.computer import ComputerTool, ToolError
from compass.tools.base import ToolResult

@pytest.fixture
def computer_tool():
    """Setup computer tool with mock display dimensions"""
    os.environ["WIDTH"] = "1920"
    os.environ["HEIGHT"] = "1080"
    return ComputerTool()

def test_screenshot_capture(computer_tool):
    """Test basic screenshot functionality"""
    result = computer_tool(action="screenshot")
    
    assert result.error is None
    assert result.output is None
    assert result.base64_image is not None
    assert isinstance(result.base64_image, str)
    
    # Updated path to be relative to backend directory
    output_dir = Path(__file__).parent.parent / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    image_data = base64.b64decode(result.base64_image)
    output_path = output_dir / "test_screenshot.png"
    
    with open(output_path, "wb") as f:
        f.write(image_data)
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_invalid_action(computer_tool):
    """Test handling of invalid actions"""
    with pytest.raises(Exception) as exc_info:
        computer_tool(action="invalid_action")
    
    assert "Action 'invalid_action' is not implemented yet" in str(exc_info.value)

def test_missing_dimensions():
    """Test handling of missing display dimensions"""
    os.environ.pop("WIDTH", None)
    os.environ.pop("HEIGHT", None)
    
    with patch('compass.tools.computer.get_screen_dimensions', return_value=(0, 0)):
        with pytest.raises(ToolError) as exc_info:
            ComputerTool()
        
        assert "Could not determine screen dimensions" in str(exc_info.value)

def test_left_click_command_verification(computer_tool):
    """Test that left click generates correct cliclick command"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        mock_shell.return_value = ToolResult(output=None, error=None)
        
        computer_tool(action="left_click", coordinate=(100, 200))
        mock_shell.assert_called_once_with("cliclick c:100,200")

def test_right_click_command_verification(computer_tool):
    """Test that right click generates correct cliclick command"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        mock_shell.return_value = ToolResult(output=None, error=None)
        
        computer_tool(action="right_click", coordinate=(150, 300))
        mock_shell.assert_called_once_with("cliclick rc:150,300")

def test_click_coordinate_validation(computer_tool):
    """Test various invalid click coordinates"""
    test_cases = [
        (None, "coordinate is required for left_click"),
        ((100,), "must be a tuple of length 2"),
        ((-10, 100), "must be a tuple of non-negative ints"),
        ((2000, 2000), "are out of bounds"),
        (("100", "200"), "must be a tuple of non-negative ints"),
    ]
    
    for coordinate, expected_error in test_cases:
        with pytest.raises(ToolError) as exc_info:
            computer_tool(action="left_click", coordinate=coordinate)
        assert expected_error in str(exc_info.value)

def test_click_edge_cases(computer_tool):
    """Test edge cases for click coordinates"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        mock_shell.return_value = ToolResult(output=None, error=None)
        
        computer_tool(action="left_click", coordinate=(0, 0))
        mock_shell.assert_called_with("cliclick c:0,0")
        
        max_x, max_y = computer_tool.width, computer_tool.height
        computer_tool(action="right_click", coordinate=(max_x, max_y))
        mock_shell.assert_called_with(f"cliclick rc:{max_x},{max_y}")

def test_click_shell_error_propagation(computer_tool):
    """Test that shell errors are properly propagated"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        mock_shell.return_value = ToolResult(error="Command failed")
        
        result = computer_tool(action="left_click", coordinate=(100, 100))
        assert result.error == "Command failed"

def test_key_command_verification(computer_tool):
    """Test that key command generates correct cliclick command"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        mock_shell.return_value = ToolResult(output=None, error=None)
        
        computer_tool(action="key", text="cmd")
        mock_shell.assert_called_once_with("cliclick kp:cmd")

def test_type_command_verification(computer_tool):
    """Test that type command generates correct cliclick command"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        mock_shell.return_value = ToolResult(output=None, error=None)
        
        computer_tool(action="type", text="Hello World")
        mock_shell.assert_called_once_with("cliclick t:'Hello World'")

def test_type_long_text_chunking(computer_tool):
    """Test that long text is properly chunked for typing"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        mock_shell.return_value = ToolResult(output=None, error=None)
        
        # Create text longer than TYPING_GROUP_SIZE
        long_text = "a" * 100  # TYPING_GROUP_SIZE is 50
        computer_tool(action="type", text=long_text)
        
        # Should be called twice with chunks
        assert mock_shell.call_count == 2
        mock_shell.assert_has_calls([
            call('cliclick t:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'),
            call('cliclick t:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        ])

def test_text_input_validation(computer_tool):
    """Test various invalid text inputs"""
    test_cases = [
        (None, {"key": "text is required for key", "type": "text is required for type"}),
        (123, {"key": "must be a string", "type": "must be a string"}),
        (["text"], {"key": "must be a string", "type": "must be a string"}),
    ]
    
    for text, expected_errors in test_cases:
        with pytest.raises(ToolError) as exc_info:
            computer_tool(action="key", text=text)
        assert expected_errors["key"] in str(exc_info.value)
        
        with pytest.raises(ToolError) as exc_info:
            computer_tool(action="type", text=text)
        assert expected_errors["type"] in str(exc_info.value)

def test_type_special_characters(computer_tool):
    """Test typing text with special characters"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        mock_shell.return_value = ToolResult(output=None, error=None)
        
        special_text = 'Hello "World"! $pecial & Ch@rs'
        computer_tool(action="type", text=special_text)
        
        # Verify the text is properly escaped
        mock_shell.assert_called_once_with("cliclick t:'Hello \"World\"! $pecial & Ch@rs'")

def test_text_input_error_propagation(computer_tool):
    """Test that shell errors are properly propagated for text input"""
    with patch.object(computer_tool, 'shell') as mock_shell:
        mock_shell.return_value = ToolResult(error="Command failed")
        
        result = computer_tool(action="type", text="test")
        assert result.error == "Command failed"
        
        result = computer_tool(action="key", text="cmd")
        assert result.error == "Command failed"