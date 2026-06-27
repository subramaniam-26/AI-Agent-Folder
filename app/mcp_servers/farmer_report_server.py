# app/mcp_servers/farmer_report_server.py
"""Farmer Report Generation MCP server.
This server orchestrates the multimodal soil analysis, nutrient statistics,
crop recommendation, and fertilizer recommendation to produce a concise
farmer-friendly report.
"""

import json
import logging
import os
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

# Ensure project root on PYTHONPATH (mirrors other servers)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Import the existing toolsets (they are defined in app.agent)
from app.agent import crop_toolset, fertilizer_toolset, multimodal_toolset, soil_toolset

logger = logging.getLogger(__name__)
server = FastMCP("farmer-report-server")


def _extract_tool_payload(response: Any) -> Any:
    """Extract JSON payload from an MCP call response when ADK wraps it."""
    if hasattr(response, "model_dump"):
        response = response.model_dump(mode="json")

    if isinstance(response, dict) and "content" in response:
        try:
            text = response["content"][0]["text"]
            return json.loads(text)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            return response

    return response


async def _call_mcp_tool(toolset, tool_name: str, arguments: dict[str, Any]) -> Any:
    """Call an MCP tool through its session manager without requiring ADK ToolContext."""
    session = await toolset._mcp_session_manager.create_session()
    response = await session.call_tool(tool_name, arguments=arguments)
    return _extract_tool_payload(response)


@server.tool()
async def generate_farmer_report(
    image_path: str, soil_type: str | None = None
) -> dict[str, Any]:
    """Generate a full farmer report from an image.

    Parameters
    ----------
    image_path: str
        Local path to the soil image.
    soil_type: str | None, optional
        Optional override for soil type. If omitted, the multimodal tool will
        estimate the closest supported dataset soil type from the image.
    """
    multimodal_args = {"image_path": image_path}
    if soil_type:
        multimodal_args["soil_type"] = soil_type
    multimodal_res = await _call_mcp_tool(
        multimodal_toolset,
        "analyze_multimodal_soil",
        multimodal_args,
    )
    if isinstance(multimodal_res, dict) and "error" in multimodal_res:
        return multimodal_res

    image_soil = multimodal_res.get("soil_type")
    dataset_soil = multimodal_res.get("closest_dataset_soil_type") or image_soil
    if not image_soil:
        return {"error": "Unable to determine soil type for report generation."}

    stats_res = await _call_mcp_tool(
        soil_toolset, "get_soil_statistics", {"soil_type": dataset_soil}
    )
    health_res = await _call_mcp_tool(
        soil_toolset, "get_soil_health_score", {"soil_type": dataset_soil}
    )

    crop_res = await _call_mcp_tool(
        crop_toolset, "get_crop_recommendation", {"soil_type": dataset_soil}
    )
    fert_res = await _call_mcp_tool(
        fertilizer_toolset,
        "get_fertilizer_recommendation",
        {"soil_type": dataset_soil},
    )

    estimated_nutrients = multimodal_res.get("estimated_nutrients", {})
    report_text = (
        f"**Image Identified Soil Type:** {image_soil}\n"
        f"**Closest Dataset Soil Type:** {dataset_soil}\n"
        f"**Soil Type Source:** {multimodal_res.get('soil_type_source', 'N/A')}\n"
        f"**Image Confidence:** {multimodal_res.get('image_confidence', 'N/A')}\n"
        f"**Image Reason:** {multimodal_res.get('reason', 'N/A')}\n"
        f"**Approximate Nutrients From Image:**\n"
        f"{estimated_nutrients or 'N/A'}\n"
        f"**Dataset Comparison (closest class, sample count {stats_res.get('sample_count', 'N/A')}):**\n"
        f"{stats_res.get('averages', 'N/A')}\n"
        f"**Estimated Soil Health From Image:** "
        f"{estimated_nutrients.get('soil_health_score', 'N/A')}\n"
        f"**Dataset Soil Health:** {health_res.get('condition_assessment', 'N/A')} "
        f"(Score {health_res.get('average_health_score', 'N/A')})\n"
        f"**Recommended Crop:** {crop_res.get('recommended_crop', 'N/A')} "
        f"(Confidence {crop_res.get('confidence', 'N/A')})\n"
        f"**Recommended Fertilizer:** {fert_res.get('recommended_fertilizer', 'N/A')} "
        f"(Confidence {fert_res.get('confidence', 'N/A')})\n"
        f"\n_The identified soil type and nutrient values are image-based "
        f"estimates, not laboratory measurements. Crop and fertilizer guidance "
        f"uses the closest dataset soil class and should be validated with "
        f"local soil testing or an agronomist before planting._"
    )

    return {
        "soil_type": image_soil,
        "closest_dataset_soil_type": dataset_soil,
        "soil_type_source": multimodal_res.get("soil_type_source"),
        "image_detected_soil_type": multimodal_res.get("image_detected_soil_type"),
        "image_confidence": multimodal_res.get("image_confidence"),
        "image_reason": multimodal_res.get("reason"),
        "visual_features": multimodal_res.get("visual_features"),
        "estimated_nutrients": estimated_nutrients,
        "dataset_nutrients": stats_res.get("averages"),
        "nutrients": estimated_nutrients,
        "sample_count": stats_res.get("sample_count"),
        "soil_health": health_res,
        "crop_recommendation": crop_res,
        "fertilizer_recommendation": fert_res,
        "report": report_text,
    }

if __name__ == "__main__":
    server.run()
