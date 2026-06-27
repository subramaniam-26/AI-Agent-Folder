# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
)
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.genai import types
from mcp.client.stdio import StdioServerParameters

from app.security import (
    detect_prompt_injection,
    enforce_mcp_access_control,
    sanitize_input_text,
)

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MCP_SERVER_DIR = PROJECT_ROOT / "app" / "mcp_servers"


def _stdio_mcp_toolset(server_filename: str) -> McpToolset:
    """Create an ADK 2.3 MCP toolset backed by a local FastMCP stdio server."""
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[str(MCP_SERVER_DIR / server_filename)],
                cwd=str(PROJECT_ROOT),
            ),
            timeout=60.0,
        ),
    )


soil_toolset = _stdio_mcp_toolset("soil_server.py")
crop_toolset = _stdio_mcp_toolset("crop_server.py")
fertilizer_toolset = _stdio_mcp_toolset("fertilizer_server.py")
multimodal_toolset = _stdio_mcp_toolset("multimodal_server.py")


def _gemini_model() -> Gemini:
    """Return the preserved Gemini model configuration for every ADK agent."""
    return Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    )


async def before_tool_callback(tool, args, tool_context):
    """Validate and sanitize MCP tool arguments before execution."""

    tool_name = getattr(tool, "name", "unknown")

    allowed, message = enforce_mcp_access_control(tool_name)
    if not allowed:
        return {"error": message}

    for key, value in args.items():
        if isinstance(value, str):
            cleaned = sanitize_input_text(value)
            if not cleaned:
                return {"error": f"Please provide a valid {key.replace('_', ' ')}."}

            detected, error_msg = detect_prompt_injection(cleaned)
            if detected:
                return {"error": error_msg}

            args[key] = cleaned

    return None


async def on_model_error_callback(callback_context, llm_request, error):
    """Return a stable user-facing response for transient Gemini failures."""
    rendered_error = str(error)
    retryable_markers = [
        "429",
        "503",
        "RESOURCE_EXHAUSTED",
        "Service Unavailable",
        "Too Many Requests",
    ]
    if not any(marker in rendered_error for marker in retryable_markers):
        return None

    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[
                types.Part.from_text(
                    text=(
                        "The Gemini model is temporarily busy or quota-limited. "
                        "Please retry the same soil question in a moment; the MCP "
                        "soil tools and dataset remain available."
                    )
                )
            ],
        )
    )


async def on_tool_error_callback(tool, args, tool_context, error):
    """Convert MCP tool failures into structured tool results."""
    tool_name = getattr(tool, "name", "unknown")
    return {
        "error": f"MCP tool '{tool_name}' failed safely.",
        "details": str(error),
    }


soil_analysis_agent = Agent(
    name="soil_analysis_agent",
    description=(
        "Answers dataset-backed questions about soil nutrient statistics, soil "
        "profiles, and soil health scores."
    ),
    model=_gemini_model(),
    instruction="""
You are the soil analysis specialist. Use soil MCP tools for every nutrient,
profile, statistics, and health-score request. Explain nitrogen, phosphorus,
potassium, sulphur, micronutrients, pH, organic carbon, electrical conductivity,
and health status in farmer-friendly language. Do not invent values or soil
types; if the tool reports an error, ask for a supported soil type.
""",
    tools=[soil_toolset],
    before_tool_callback=before_tool_callback,
    on_model_error_callback=on_model_error_callback,
    on_tool_error_callback=on_tool_error_callback,
)

crop_recommendation_agent = Agent(
    name="crop_recommendation_agent",
    description="Recommends crops for a known soil type using the crop MCP server.",
    model=_gemini_model(),
    instruction="""
You are the crop recommendation specialist. Use crop MCP tools whenever a user
asks what crop to grow for a soil type. Keep the recommendation practical and
dataset-backed, and include confidence or supporting profile details when the
tool provides them. Never guess a crop for an unsupported soil type.
""",
    tools=[crop_toolset],
    before_tool_callback=before_tool_callback,
    on_model_error_callback=on_model_error_callback,
    on_tool_error_callback=on_tool_error_callback,
)

fertilizer_recommendation_agent = Agent(
    name="fertilizer_recommendation_agent",
    description=(
        "Recommends fertilizers for a known soil type using the fertilizer MCP "
        "server."
    ),
    model=_gemini_model(),
    instruction="""
You are the fertilizer recommendation specialist. Use fertilizer MCP tools for
fertilizer, amendment, and nutrient-support questions. Explain recommendations
plainly for farmers and include confidence or profile details when available.
Never create fertilizer advice without MCP tool data.
""",
    tools=[fertilizer_toolset],
    before_tool_callback=before_tool_callback,
    on_model_error_callback=on_model_error_callback,
    on_tool_error_callback=on_tool_error_callback,
)

multimodal_soil_agent = Agent(
    name="multimodal_soil_agent",
    description=(
        "Analyzes uploaded soil images through the multimodal MCP server and "
        "estimates the closest supported dataset soil type."
    ),
    model=_gemini_model(),
    instruction="""
You are the multimodal soil specialist. Use the multimodal MCP tool for uploaded
soil images. The image-only tool estimates soil type and approximate nutrients
from visual cues, then provides the closest dataset soil class for comparison.
Treat those values as intelligent image-based estimates, not laboratory
measurements.
""",
    tools=[multimodal_toolset],
    before_tool_callback=before_tool_callback,
    on_model_error_callback=on_model_error_callback,
    on_tool_error_callback=on_tool_error_callback,
)

farmer_report_agent = Agent(
    name="farmer_report_agent",
    description=(
        "Combines soil, crop, fertilizer, and optional image-analysis results "
        "into a farmer-friendly report."
    ),
    model=_gemini_model(),
    instruction="""
You are the report specialist. Build concise farmer-friendly reports with these
headings when relevant: Soil Summary, Health Assessment, Crop Recommendation,
Fertilizer Recommendation, and Next Steps. Use specialist agents or MCP-backed
tool results. You may use image-derived approximate nutrient estimates returned
by the multimodal MCP tool, but label them as estimates and do not present them
as lab measurements.
""",
    tools=[
        soil_toolset,
        crop_toolset,
        fertilizer_toolset,
        multimodal_toolset,
    ],
    before_tool_callback=before_tool_callback,
    on_model_error_callback=on_model_error_callback,
    on_tool_error_callback=on_tool_error_callback,
)


root_agent = Agent(
    name="root_agent",
    description="Coordinates the Soil Nutrient Analysis multi-agent workflow.",
    model=_gemini_model(),
    instruction="""
You are the coordinator for a Soil Nutrient Analysis Agent used by farmers and
agricultural advisors.

Delegate to the specialist agents:
- soil_analysis_agent for soil properties, profiles, statistics, and health.
- crop_recommendation_agent for crop recommendations.
- fertilizer_recommendation_agent for fertilizer recommendations.
- multimodal_soil_agent for uploaded soil image analysis.
- farmer_report_agent for full farmer-friendly reports.

The specialists use MCP servers and image-derived analysis. Use approximate
nutrient estimates when the multimodal MCP tool returns them, but label them as
visual estimates. Do not present estimates as lab measurements. If a text-only
soil type is missing or not found, ask for a supported soil type instead of
guessing. Always explain that guidance should be validated with local soil
testing or an agronomist for high-stakes decisions.
""",
    sub_agents=[
        soil_analysis_agent,
        crop_recommendation_agent,
        fertilizer_recommendation_agent,
        multimodal_soil_agent,
        farmer_report_agent,
    ],
    before_tool_callback=before_tool_callback,
    on_model_error_callback=on_model_error_callback,
    on_tool_error_callback=on_tool_error_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
