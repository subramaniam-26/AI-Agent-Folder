# Technical Architecture - SoilSense AI

This document details the system design, components, and workflows of the SoilSense AI application.

---

## Overall Architecture

The application follows a standard multi-tier architecture with browser-based client storage:

```mermaid
graph TD
    User([User / Farmer]) -->|Interact| Frontend["Frontend (static/index.html)"]
    Frontend -->|Local Storage| BrowserDB[("Browser Local Storage (History & Chat)")]
    Frontend -->|POST /report, POST /chat| FastAPI["FastAPI Backend (main.py)"]
    FastAPI -->|Coordinates| ADK["Google ADK Root Agent (Gemini)"]
    ADK -->|Tools Connection| MCPServers["FastMCP Servers (multimodal, crop, fertilizer)"]
    MCPServers -->|Reads Database| Dataset[("CSV Database (soil_data.csv)")]
```

---

## Agent Workflow

The Root Coordinator Agent routes tasks dynamically to specialist sub-agents using a ReAct reasoning loop:

```mermaid
graph TD
    Request[User Input or Photo] --> Coordinator["Root Agent (Coordinator)"]
    Coordinator -->|Vision Classification| SubVision["Multimodal Soil Sub-Agent"]
    Coordinator -->|Property Calculations| SubSoil["Soil Analysis Sub-Agent"]
    Coordinator -->|Crop Suitability| SubCrop["Crop Recommendation Sub-Agent"]
    Coordinator -->|Nutrient Balancing| SubFert["Fertilizer Sub-Agent"]
    
    SubVision --> Tools["Specialist Python Tools & Heuristics"]
    SubSoil --> Tools
    SubCrop --> Tools
    SubFert --> Tools
```

---

## Image Analysis Flow

The image diagnostic pipeline utilizes visual heuristics followed by database queries:

```mermaid
graph TD
    Upload[Upload Soil Photo] --> Base64[Convert to Base64 Thumbnail for Local Storage]
    Upload --> Stats["Calculate HSV/RGB Color, Texture, Brightness Heuristics"]
    Stats --> Estimate["Estimate Soil Class (e.g. Laterite, Red Loam)"]
    Estimate --> Reference["Lookup Nearest Dataset Soil Statistics"]
    Reference --> Cards["Format Nutrients Grid, Score Circle & Recommendation Cards"]
    Cards --> Save[Save analysis record to browser history]
```

---

## Farmer Assistant Flow

The conversational chatbot provides context-aware assistance by combining local reports with questions:

```mermaid
graph TD
    Question[User asks: 'What fertilizer should I apply?'] --> Active["Retrieve Active Soil Report from local storage"]
    Active --> Context["Prepend report parameters as background context metadata"]
    Context --> Query["Send context-enhanced query to backend /chat endpoint"]
    Query --> Gemini["Gemini Agent interprets question with soil properties context"]
    Gemini --> Bubble["Render chat bubble in Assistant Interface"]
    Bubble --> Save[Save dialogue record to Chat History]
```
