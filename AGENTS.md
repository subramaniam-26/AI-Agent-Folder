# AI Agent Architecture - SoilSense AI

This document explains the AI agent system driving SoilSense AI. The project is built using the **Google Agent Development Kit (ADK)** and coordinates multiple specialist sub-agents and toolsets.

---

## Purpose

The core purpose of the AI Agent is to act as a digital agronomist. It translates visual data from a soil photo and statistical data from local databases into simple, actionable recommendations for farmers.

---

## Agent Workflow

SoilSense AI uses a hierarchical coordinator-specialist agent pattern:

1. **Root Agent (`root_agent`)**: Coordinates user requests. It routes tasks to specialized sub-agents based on the user's intent.
2. **Specialist Sub-Agents**:
   - `multimodal_soil_agent`: Handles image input and coordinates visual estimations.
   - `soil_analysis_agent`: Inspects soil properties and health ratings.
   - `crop_recommendation_agent`: Chooses suited crops for the soil.
   - `fertilizer_recommendation_agent`: Suggests fertilizer balances.
   - `farmer_report_agent`: Formulates final written guidance logs.

---

## Agent Skills

Skills represent specialized blocks of Python logic registered as tools for the agents:
- **`image_validation`**: Pre-validates uploaded files (dimensions, extension, format checks).
- **`multimodal_soil_analysis`**: Evaluates RGB/HSV color, brightness, and texture variances to estimate soil types deterministically.

---

## Gemini Integration

SoilSense AI uses **Google Gemini** as the core cognitive model to power the ReAct reasoning loops:
- Gemini interprets conversational questions in the Farmer Assistant.
- It parses user intent, executes appropriate MCP tools, and synthesizes developer-friendly payloads into simple instructions.

---

## MCP Servers

Model Context Protocol (MCP) servers act as decoupled data nodes. SoilSense AI runs four FastMCP servers:
- **`soil-server`**: Computes database means and health scores.
- **`crop-server`**: Evaluates suited crop varieties based on historical database occurrences.
- **`fertilizer-server`**: Suggests nutrient mixtures based on soil types.
- **`multimodal-server`**: Hosts the visual classification tool.

---

## Dataset Reference

All MCP servers query [soil_data.csv](file:///home/venkat/soil-nutrient-analyzer/dataset/soil_data.csv) in the `dataset/` folder. This database contains regional records of soil types, macronutrient/micronutrient stats, and recommended crop-fertilizer pairings.

---

## Farmer Assistant

The Farmer Assistant chatbot (`chat.html`) enables natural conversation:
- Uses client-side Local Storage to preserve past conversation message logs.
- Automatically injects the currently open report as context before sending questions to Gemini, making the agent context-aware.

---

## Translation Helpers

The backend supports translating responses to Hindi (`hi`) and Telugu (`te`) using preconfigured translations in the FastAPI routing layers (`app/api/main.py`), making it accessible to regional farmers.

---

## Security Layer

Security hooks protect the agent from common vulnerabilities:
- **Prompt Injection Callback**: A before-tool check blocks commands containing prompt injection patterns.
- **MCP Access Control**: Restricts unauthorized tool executions (like agent state transfers).
