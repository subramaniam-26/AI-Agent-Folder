# app/mcp_servers/multimodal_server.py
"""Multimodal Soil Analysis MCP server.

Provides a tool `analyze_multimodal_soil` that accepts an image path, estimates
soil type from image color/texture cues, and returns approximate nutrient values
with an optional dataset comparison for the closest supported soil.
"""

import os
import pathlib
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP
from PIL import Image, ImageStat

# Ensure the project root is on PYTHONPATH (mirrors soil_server implementation)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.dataset_layer import DatasetLayer
from app.utils import logger  # reuse logger defined in utils.py

server = FastMCP("multimodal-server")

# Instantiate the dataset layer (same as other servers)
_db = DatasetLayer()


def _image_color_stats(image_path: pathlib.Path) -> dict[str, float]:
    """Return simple RGB/HSV statistics for image-only soil estimation."""
    with Image.open(image_path) as image:
        rgb_image = image.convert("RGB").resize((128, 128))
        stat = ImageStat.Stat(rgb_image)
        red, green, blue = [value / 255 for value in stat.mean]
        red_std, green_std, blue_std = [value / 255 for value in stat.stddev]

        hsv = rgb_image.convert("HSV")
        hsv_stat = ImageStat.Stat(hsv)
        hue, saturation, _value = [value / 255 for value in hsv_stat.mean]

    brightness = (red + green + blue) / 3
    redness = red - ((green + blue) / 2)
    yellowness = ((red + green) / 2) - blue
    darkness = 1 - brightness
    texture_variation = (red_std + green_std + blue_std) / 3
    return {
        "red": round(red, 3),
        "green": round(green, 3),
        "blue": round(blue, 3),
        "hue": round(hue, 3),
        "saturation": round(saturation, 3),
        "brightness": round(brightness, 3),
        "redness": round(redness, 3),
        "yellowness": round(yellowness, 3),
        "darkness": round(darkness, 3),
        "texture_variation": round(texture_variation, 3),
    }


def _infer_soil_type_from_image(image_path: pathlib.Path) -> dict[str, Any]:
    """Estimate a soil type from image color cues.

    This is a deterministic image heuristic, not a trained classifier. The
    result can be broader than the project dataset; ``closest_dataset_soil_type``
    tells downstream tools which dataset row is best for comparison.
    """
    stats = _image_color_stats(image_path)
    brightness = stats["brightness"]
    saturation = stats["saturation"]
    redness = stats["redness"]
    yellowness = stats["yellowness"]
    darkness = stats["darkness"]
    texture = stats["texture_variation"]

    if brightness > 0.74 and saturation < 0.16:
        soil_type = "Chalky Soil"
        closest_dataset_soil_type = "Saline Soil"
        reason = "very pale, low-saturation surface color"
        confidence = min(0.82, 0.5 + brightness * 0.28)
    elif brightness > 0.68 and saturation < 0.2:
        soil_type = "Saline Soil"
        closest_dataset_soil_type = "Saline Soil"
        reason = "pale low-saturation surface color"
        confidence = min(0.78, 0.48 + brightness * 0.25)
    elif darkness > 0.62 and saturation > 0.18:
        soil_type = "Black Cotton"
        closest_dataset_soil_type = "Black Cotton"
        reason = "dark image tone with enough color saturation"
        confidence = min(0.9, 0.58 + darkness * 0.32)
    elif darkness > 0.56:
        soil_type = "Peaty"
        closest_dataset_soil_type = "Peaty"
        reason = "very dark organic-looking soil tone"
        confidence = min(0.86, 0.55 + darkness * 0.28)
    elif redness > 0.16 and saturation > 0.32:
        soil_type = "Red Loam"
        closest_dataset_soil_type = "Red Loam"
        reason = "strong red-brown color response"
        confidence = min(0.88, 0.56 + redness + saturation * 0.18)
    elif redness > 0.09 and brightness > 0.42:
        soil_type = "Red Sandy"
        closest_dataset_soil_type = "Red Sandy"
        reason = "lighter reddish sandy-looking color"
        confidence = min(0.82, 0.52 + redness + brightness * 0.18)
    elif yellowness > 0.12 and saturation > 0.28:
        soil_type = "Laterite"
        closest_dataset_soil_type = "Laterite"
        reason = "yellow-red lateritic color response"
        confidence = min(0.8, 0.5 + yellowness + saturation * 0.2)
    elif texture > 0.24 and brightness > 0.46:
        soil_type = "Rocky or Gravelly Soil"
        closest_dataset_soil_type = "Sandy Loam"
        reason = "high visible texture variation and lighter soil tone"
        confidence = min(0.74, 0.48 + texture)
    elif brightness > 0.58:
        soil_type = "Sandy Loam"
        closest_dataset_soil_type = "Sandy Loam"
        reason = "light brown soil color"
        confidence = min(0.76, 0.5 + brightness * 0.2)
    elif saturation < 0.16:
        soil_type = "Silty Soil" if brightness > 0.48 else "Clay"
        closest_dataset_soil_type = "Clay"
        reason = "muted grey-brown soil color"
        confidence = 0.62
    elif brightness < 0.48:
        soil_type = "Clay Loam"
        closest_dataset_soil_type = "Clay Loam"
        reason = "medium-dark brown soil color"
        confidence = 0.66
    else:
        soil_type = "Loamy Soil"
        closest_dataset_soil_type = "Alluvial"
        reason = "balanced brown soil color"
        confidence = 0.6

    return {
        "soil_type": soil_type,
        "closest_dataset_soil_type": closest_dataset_soil_type,
        "image_confidence": round(confidence, 3),
        "visual_features": stats,
        "inference_method": "image_color_heuristic",
        "reason": reason,
    }


def _estimate_nutrients_from_image(
    visual_features: dict[str, float], soil_type: str
) -> dict[str, float]:
    """Estimate approximate nutrient values from visual cues.

    These values are agronomic heuristics for farmer guidance. They are not lab
    measurements and are intentionally marked separately from dataset values.
    """
    brightness = visual_features["brightness"]
    darkness = visual_features["darkness"]
    redness = max(visual_features["redness"], 0)
    saturation = visual_features["saturation"]
    texture = visual_features["texture_variation"]

    nitrogen = 150 + darkness * 260 + saturation * 60
    phosphorus = 8 + brightness * 24 - redness * 10
    potassium = 120 + darkness * 150 + redness * 140
    sulphur = 8 + saturation * 22
    organic_carbon = 0.35 + darkness * 1.25
    ph = 6.6 + (brightness - 0.5) * 1.8 - redness * 0.8
    electrical_conductivity = 0.18 + max(brightness - 0.6, 0) * 1.8
    iron = 3.5 + redness * 18
    zinc = 0.55 + saturation * 1.2
    copper = 0.35 + saturation * 0.7
    boron = 0.25 + brightness * 0.45
    magnesium = 45 + darkness * 55

    soil_adjustments = {
        "Peaty": {"nitrogen": 90, "organic_carbon": 1.2, "ph": -0.4},
        "Black Cotton": {"potassium": 90, "magnesium": 35, "ph": 0.25},
        "Sandy Loam": {"nitrogen": -40, "potassium": -30, "organic_carbon": -0.15},
        "Red Sandy": {"nitrogen": -55, "phosphorus": -4, "iron": 5},
        "Laterite": {"phosphorus": -5, "iron": 7, "ph": -0.25},
        "Saline Soil": {"electrical_conductivity": 1.6, "ph": 0.45},
        "Chalky Soil": {"ph": 0.8, "iron": -1.2, "zinc": -0.2},
        "Clay": {"potassium": 45, "magnesium": 20},
        "Clay Loam": {"potassium": 35, "organic_carbon": 0.1},
        "Silty Soil": {"phosphorus": 4, "organic_carbon": 0.05},
        "Rocky or Gravelly Soil": {"nitrogen": -60, "phosphorus": -3, "organic_carbon": -0.25},
    }

    values = {
        "nitrogen": nitrogen,
        "phosphorus": phosphorus,
        "potassium": potassium,
        "sulphur": sulphur,
        "iron": iron,
        "zinc": zinc,
        "copper": copper,
        "boron": boron,
        "magnesium": magnesium,
        "ph": ph,
        "organic_carbon": organic_carbon,
        "electrical_conductivity": electrical_conductivity,
    }
    for nutrient, adjustment in soil_adjustments.get(soil_type, {}).items():
        values[nutrient] += adjustment

    values["soil_health_score"] = (
        45
        + min(values["organic_carbon"], 2.2) * 14
        + (8 if 6.2 <= values["ph"] <= 7.5 else -6)
        - max(values["electrical_conductivity"] - 1.0, 0) * 8
        - texture * 8
    )

    ranges = {
        "nitrogen": (40, 520),
        "phosphorus": (3, 60),
        "potassium": (50, 520),
        "sulphur": (4, 45),
        "iron": (1, 35),
        "zinc": (0.2, 4),
        "copper": (0.1, 3),
        "boron": (0.1, 2),
        "magnesium": (15, 160),
        "ph": (4.5, 9.0),
        "organic_carbon": (0.15, 4),
        "electrical_conductivity": (0.05, 4),
        "soil_health_score": (10, 95),
    }
    return {
        key: round(min(max(value, low), high), 2)
        for key, value in values.items()
        for low, high in [ranges[key]]
    }


@server.tool()
async def analyze_multimodal_soil(
    image_path: str, soil_type: str | None = None
) -> dict[str, Any]:
    """Analyze soil from an image, with an optional user-provided override.

    Parameters
    ----------
    image_path: str
        Path to a local image file (e.g., drone photo, satellite tile).
    soil_type: str | None, optional
        Optional override. If omitted, the tool estimates soil type from image
        color cues and only uses the closest dataset soil for comparison.

    Returns
    -------
    dict
        A dictionary containing:
        * ``soil_type`` - image-estimated soil name
        * ``estimated_nutrients`` - approximate image-derived nutrient values
        * ``dataset_averages`` - closest dataset averages when available
        * ``image_confidence`` - confidence score (0-1) from image inference
    """
    img_path = pathlib.Path(image_path)
    if not img_path.is_file():
        return {"error": f"Image file not found: {image_path}"}

    try:
        from app.utils import normalize_soil_type
    except Exception as exc:
        logger.exception("[MULTIMODAL] Failed to import normalization utility")
        return {"error": f"Multimodal dependencies are unavailable: {exc}"}

    try:
        image_estimate = _infer_soil_type_from_image(img_path)
    except Exception as exc:
        logger.exception("[MULTIMODAL] Failed to analyze image")
        return {"error": f"Unable to analyze image: {exc}"}

    detected_soil_type = image_estimate["soil_type"]
    dataset_soil_type = image_estimate["closest_dataset_soil_type"]
    if soil_type:
        dataset_soil_type = normalize_soil_type(soil_type)
        detected_soil_type = dataset_soil_type

    stats = _db.get_soil_statistics(dataset_soil_type)
    dataset_averages = None if "error" in stats else stats["averages"]
    sample_count = 0 if "error" in stats else stats.get("sample_count", 0)
    estimated_nutrients = _estimate_nutrients_from_image(
        image_estimate["visual_features"], detected_soil_type
    )

    enriched = {
        "soil_type": detected_soil_type,
        "image_detected_soil_type": image_estimate["soil_type"],
        "closest_dataset_soil_type": dataset_soil_type,
        "estimated_nutrients": estimated_nutrients,
        "dataset_averages": dataset_averages,
        "averages": estimated_nutrients,
        "sample_count": sample_count,
        "image_confidence": image_estimate["image_confidence"],
        "inference_method": image_estimate["inference_method"],
        "visual_features": image_estimate["visual_features"],
        "reason": image_estimate["reason"],
        "nutrient_estimation_source": "image_visual_heuristic",
        "note": (
            "Nutrient values are approximate image-based estimates, not lab "
            "measurements. Dataset values are included only as comparison when "
            "a closest soil class is available."
        ),
        "soil_type_source": "user_override" if soil_type else "image_only",
    }
    logger.info(
        "[MULTIMODAL] soil_type=%s closest_dataset=%s source=%s confidence=%.3f",
        detected_soil_type,
        dataset_soil_type,
        enriched["soil_type_source"],
        enriched["image_confidence"],
    )
    return enriched


if __name__ == "__main__":
    server.run()
