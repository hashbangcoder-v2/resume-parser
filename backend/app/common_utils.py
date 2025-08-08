import base64
import io
from PIL import Image
from pathlib import Path
from functools import lru_cache

def image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')


@lru_cache(maxsize=1)
def get_system_prompt() -> str:
    # This path is relative to the current file, which is more robust.
    prompt_path = Path(__file__).parent / "prompts" / "resume_analyzer.txt"
    with open(prompt_path, "r") as f:
        return f.read()
