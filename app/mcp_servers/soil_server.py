import os
import sys

from mcp.server.fastmcp import FastMCP

# Ensure the root of the project is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.dataset_layer import DatasetLayer
from app.utils import logger, normalize_soil_type

server = FastMCP("soil-server")
db = DatasetLayer()

@server.tool()
async def get_soil_statistics(soil_type: str) -> dict:
    """Retrieves average values of soil properties for the specified soil type.

    Args:
        soil_type: User-provided soil type (may contain whitespace, different case, or the word "soil").
    """
    raw_input = soil_type
    normalized = normalize_soil_type(soil_type)
    stats = db.get_soil_statistics(normalized)
    logger.info("[SOIL_SERVER] get_soil_statistics - raw: %s | normalized: %s", raw_input, normalized)
    return stats

@server.tool()
async def get_soil_health_score(soil_type: str) -> dict:
    """Retrieves health scores for the specified soil type.

    Args:
        soil_type: User-provided soil type.
    """
    raw_input = soil_type
    normalized = normalize_soil_type(soil_type)
    logger.info("[SOIL_SERVER] get_soil_health_score - raw: %s | normalized: %s", raw_input, normalized)
    health = db.get_soil_health_score(normalized)
    return health

@server.tool()
async def get_soil_profile(soil_type: str) -> list[dict]:
    """Retrieves raw profiles for the specified soil type.

    Args:
        soil_type: User-provided soil type.
    """
    raw_input = soil_type
    normalized = normalize_soil_type(soil_type)
    logger.info("[SOIL_SERVER] get_soil_profile - raw: %s | normalized: %s", raw_input, normalized)
    profile = db.get_soil_profile(normalized)
    return profile

if __name__ == "__main__":
    server.run()
