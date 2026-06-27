import os
import sys

from mcp.server.fastmcp import FastMCP

# Ensure the root of the project is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.dataset_layer import DatasetLayer
from app.utils import logger, normalize_soil_type

server = FastMCP("fertilizer-server")
db = DatasetLayer()

@server.tool()
async def get_fertilizer_recommendation(soil_type: str) -> dict:
    """Retrieves dataset-driven fertilizer recommendation for the specified soil type, along with a confidence level and historical frequency distribution.

    Args:
        soil_type: The name of the soil type (e.g. Peaty, Clay Loam, Alluvial, Black Cotton, Saline Soil, Clay, Red Sandy, Red Loam, Laterite, Sandy Loam).
    """
    normalized = normalize_soil_type(soil_type)
    logger.info("[FERTILIZER_SERVER] get_fertilizer_recommendation - raw: %s | normalized: %s", soil_type, normalized)
    rec = db.get_fertilizer_recommendation(normalized)
    return rec

@server.tool()
async def get_fertilizer_profile(fertilizer_name: str) -> dict:
    """Retrieves the typical soil nutrient profile and primary soil types associated with the recommendation and application of the specified fertilizer.

    Args:
        fertilizer_name: The name of the fertilizer (e.g. Gypsum, Organic Manure, DAP, NPK 17:17:17, NPK 19:19:19, Vermicompost, Potash, Urea, NPK 20:20:0, Compost).
    """
    profile = db.get_fertilizer_profile(fertilizer_name)
    return profile

if __name__ == "__main__":
    server.run()
