import os
import sys

from mcp.server.fastmcp import FastMCP

# Ensure the root of the project is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.dataset_layer import DatasetLayer
from app.utils import logger, normalize_soil_type

server = FastMCP("crop-server")
db = DatasetLayer()

@server.tool()
async def get_crop_recommendation(soil_type: str) -> dict:
    """Retrieves dataset-driven crop recommendation for the specified soil type, along with a confidence level and historical frequency distribution.

    Args:
        soil_type: The name of the soil type (e.g. Peaty, Clay Loam, Alluvial, Black Cotton, Saline Soil, Clay, Red Sandy, Red Loam, Laterite, Sandy Loam).
    """
    normalized = normalize_soil_type(soil_type)
    logger.info("[CROP_SERVER] get_crop_recommendation - raw: %s | normalized: %s", soil_type, normalized)
    rec = db.get_crop_recommendation(normalized)
    return rec

@server.tool()
async def get_crop_profile(crop_name: str) -> dict:
    """Retrieves typical growing conditions (nitrogen, phosphorus, potassium, ph, organic carbon, and health score averages) and preferred soil types where the specified crop has historically been recommended in the dataset.

    Args:
        crop_name: The name of the crop (e.g. Wheat, Tea, Rice, Cotton, Maize, Banana, Coffee, pulses, Barley, Sugarcane, Cashew, Soybean).
    """
    profile = db.get_crop_profile(crop_name)
    return profile

if __name__ == "__main__":
    server.run()
