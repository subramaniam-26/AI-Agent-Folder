import json
import os

from app.security import log_audit
from app.skills.image_validation import validate_image_file


def analyze_soil_image(filename: str, image_bytes: bytes) -> dict:
    """Analyze a soil image and return detected soil type and confidence.

    Parameters:
        filename: Name of the uploaded image file.
        image_bytes: Raw bytes of the image.

    Returns:
        dict with keys:
            "soil_type": str - predicted soil type (e.g., "Sandy Loam").
            "confidence": float - model confidence (0.0-1.0).
            "reasoning": str - brief explanation of the prediction.
            "error": str (optional) - error message if validation or model call fails.
    """
    # Validate the image first
    validation = validate_image_file(filename, image_bytes)
    if not validation.get("valid"):
        error_msg = validation.get("reason", "Invalid image.")
        log_audit("soil_analysis", "REJECT", error_msg)
        return {"error": error_msg}

    try:
        import google.generativeai as genai
    except ImportError:
        err_msg = "Optional dependency google-generativeai is not installed."
        log_audit("soil_analysis", "ERROR", err_msg)
        return {"error": err_msg}

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        err_msg = "GOOGLE_API_KEY is not configured."
        log_audit("soil_analysis", "ERROR", err_msg)
        return {"error": err_msg}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        # Prepare the image for the Gemini model
        image = genai.upload_file(content=image_bytes, mime_type="image/jpeg")
        # Prompt for soil type detection
        prompt = (
            "You are an agricultural expert. Analyze the provided soil image and "
            "identify the soil type (e.g., sandy, loamy, clay) and give a confidence score. "
            "Provide a short reasoning (one sentence). Return JSON with keys "
            "'soil_type', 'confidence', and 'reasoning'."
        )
        response = model.generate_content([prompt, image])
        # The model returns a string; attempt to parse JSON
        content = response.text.strip()
        # Simple safety parsing - expect JSON-like output
        result = json.loads(content)
        # Ensure required keys exist
        if not all(k in result for k in ("soil_type", "confidence", "reasoning")):
            raise ValueError("Missing expected keys in model output")
        log_audit("soil_analysis", "PASS", f"Image '{filename}' analyzed successfully.")
        return result
    except Exception as e:
        # Log and return error information
        err_msg = f"Soil analysis failed: {e}"
        log_audit("soil_analysis", "ERROR", err_msg)
        return {"error": err_msg}
