# SoilSense AI - Soil Nutrient Analyzer AI Agent

SoilSense AI is an agentic AI application designed to estimate soil conditions, approximate nutrient levels, recommend crop choices, suggest fertilizers, and answer farmers' questions using a conversational assistant. It is built as a college capstone project for the Kaggle AI Agents competition.

---

## Introduction

In modern agriculture, understanding soil characteristics is crucial for farmers to determine what crop to sow and how much fertilizer to apply. Traditional laboratory soil testing is slow, expensive, and inaccessible in remote regions. SoilSense AI addresses this by providing instant diagnostic reports directly from smartphone soil photos.

---

## Problem Statement

Smallholder farmers often lack the tools to measure soil health quickly. Without this information, they struggle to:
- Select the best crops for their specific soil type.
- Apply the correct type and quantity of fertilizers, leading to soil degradation or low crop yields.
- Get instant answers to agronomical questions in their preferred language.

---

## Project Objectives

- **Visual Estimation**: Implement simple color and texture heuristics to classify soil types from photos.
- **Macronutrient & Micronutrient Profiling**: Estimate essential nutrients (Nitrogen, Phosphorus, Potassium, etc.) based on visual properties.
- **Data-Driven Crop & Fertilizer Guidance**: Compare visual results with real regional database averages using Model Context Protocol (MCP) servers.
- **Agentic Conversational Support**: Build a farmer assistant chatbot capable of answering questions about soil diagnostics.
- **Offline Client Persistence**: Save reports, images, and chat history locally using browser storage so no database setup is required.

---

## Features

- **Soil Photo Upload**: Support drag-and-drop image uploads with live preview.
- **Macronutrient & Micronutrient Estimation**: Generates levels for 12 key soil parameters (Nitrogen, Phosphorus, Potassium, Sulphur, Iron, Zinc, Copper, Boron, Magnesium, pH, Organic Carbon, Electrical Conductivity).
- **Interactive Circular Health Score**: Gauges overall soil health on a visual dial.
- **Crop & Fertilizer Matches**: Dynamic crop suggestions based on the database statistics.
- **Farmer Chat Advisor**: A context-aware conversational chatbot using Gemini.
- **Analysis History Dashboard**: Search, filter, and review previous soil analysis records.
- **Export & Download**: Export history data as JSON files or download individual farmer reports as PDFs.

---

## Technology Stack

- **Framework**: FastAPI (Python) for API endpoints and static file hosting.
- **AI Agent System**: Google Agent Development Kit (ADK) to coordinate specialist sub-agents.
- **LLM Engine**: Google Gemini.
- **MCP Servers**: Model Context Protocol servers for crop, fertilizer, and soil database operations.
- **Client Frontend**: Clean responsive HTML, CSS (Vanilla), and JavaScript.
- **Storage**: Browser Local Storage for persistent history.

---

## Project Structure

```
soil-nutrient-analyzer/
├── app/
│   ├── agent.py               # Root ADK agent setup
│   ├── dataset_layer.py       # Helper class to query the database CSV
│   ├── security.py            # Security callbacks and validations
│   ├── utils.py               # Text processing utilities
│   ├── skills/                # ADK specialist skills
│   ├── mcp_servers/           # FastMCP server implementations
│   ├── app_utils/             # telemetry and configuration utilities
│   └── prompts/               # System instruction prompt directories
├── dataset/
│   └── soil_data.csv          # Regional soil statistics database CSV
├── static/
│   ├── css/                   # Stylesheet folder (reserved)
│   ├── js/                    # Script folder (reserved)
│   ├── images/                # Icon and image assets
│   ├── index.html             # Analysis interface
│   ├── chat.html              # Farmer Assistant page
│   └── history.html           # History Dashboard page
├── docs/                      # Technical manuals
├── screenshots/               # Interface preview figures
├── tests/                     # Unit and Integration test scripts
├── README.md                  # Main project introduction
├── AGENTS.md                  # AI Agent definition manual
├── ARCHITECTURE.md            # Technical workflow charts
├── DEPLOYMENT.md              # Installation instructions
├── SECURITY.md                # Safety safeguards manual
├── LICENSE                    # MIT License file
├── .env.example               # Config template
└── pyproject.toml             # Python build dependencies
```

---

## How to Run

1. **Install Dependencies**:
   ```bash
   uv tool install google-agents-cli
   agents-cli install
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and enter your Google API key:
   ```bash
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

3. **Start the Web Server**:
   ```bash
   uv run python app/api/main.py
   ```
   Open your browser and navigate to [http://localhost:8000](http://localhost:8000).

---

## Screenshots

*(See the `/screenshots` directory for placeholders)*
- Contains the screenshots of the working agent
- has images of components like Home page, Analysis dashboard, History etc,
---

## Future Improvements

- Add trained CNN classifiers for higher visual soil identification accuracy.
- Integrate regional weather forecasting API.
- Support offline progressive web app (PWA) installation.

---

## Author

**Venkata Subramaniam S K**  
College AI Agents Capstone Project Submission  
Kaggle AI Agents Capstone Competition  
License: MIT  
