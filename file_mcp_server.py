import base64
import os
import logging
from fastmcp.server import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("file_mcp_server")

# Initialize FastMCP server
mcp = FastMCP("file_mcp_server")

@mcp.tool()
def list_files(directory: str = ".") -> list[str]:
    """Lists all files and directories within a specified directory."""
    try:
        return os.listdir(directory)
    except FileNotFoundError:
        return [f"Error: Directory '{directory}' not found."]

@mcp.tool()
def read_file(filepath: str) -> str:
    """Reads the content of a specified file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File '{filepath}' not found."
    except Exception as e:
        return f"Error reading file '{filepath}': {e}"

@mcp.tool()
def analyze_image(filepath: str) -> str:
    """Analyze image files and describe their content."""
    try:
        from PIL import Image
        
        # Check if file exists
        if not os.path.exists(filepath):
            return f"Error: File '{filepath}' not found."
            
        # Open and analyze image
        with Image.open(filepath) as img:
            width, height = img.size
            format_type = img.format
            mode = img.mode
            
            # Basic image analysis
            analysis = f"""
Image Analysis Results:
- Dimensions: {width} x {height} pixels
- Format: {format_type}
- Color Mode: {mode}
- File Size: {os.path.getsize(filepath)} bytes
- File Path: {filepath}
"""
            return analysis
            
    except ImportError:
        return "Error: PIL library required for image analysis. Install with: pip install Pillow"
    except Exception as e:
        return f"Error analyzing image '{filepath}': {e}"

@mcp.tool()
def search_files(directory: str, keyword: str) -> list[str]:
    """Searches for files containing a specific keyword within a directory."""
    found_files = []
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        if keyword in f.read():
                            found_files.append(filepath)
                except Exception:
                    # Ignore files that cannot be read (e.g., binary files)
                    pass
        return found_files
    except FileNotFoundError:
        return [f"Error: Directory '{filepath}' not found."]

@mcp.tool()
def analyze_image_with_claude(filepath: str) -> str:
    """Analyze image content using Claude's vision capabilities."""
    try:
        # Read image as binary and encode as base64
        with open(filepath, 'rb') as f:
            image_bytes = f.read()
            base64_data = base64.b64encode(image_bytes).decode('utf-8')
        
        return f"""
IMAGE_READY_FOR_ANALYSIS:
Filename: {os.path.basename(filepath)}
File Size: {len(image_bytes)} bytes
Base64 Data: {base64_data}

Use this image data with a multimodal model like Claude to analyze the visual content.
"""
            
    except Exception as e:
        return f"Error processing image: {e}"

# Entry point to run the server
if __name__ == "__main__":
    logger.info("Starting MCP file server with image analysis...")
    mcp.run(transport="sse", host="0.0.0.0", port=8080)
