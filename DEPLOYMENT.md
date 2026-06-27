# Deployment Guide - SoilSense AI

This document provides simple step-by-step instructions to run SoilSense AI locally and deploy it to Google Cloud Run.

---

## Prerequisites

Ensure you have the following installed on your system:
- **Python**: Version 3.11 or 3.12.
- **uv**: Python package manager. If you don't have it, install it using:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Google Cloud SDK (gcloud CLI)**: Required only if you want to deploy to Google Cloud.

---

## Step 1: Install Dependencies

Clone the project and install all required libraries using `uv`:

```bash
# Install the Google Agents CLI tool
uv tool install google-agents-cli

# Install python dependencies
agents-cli install
```

---

## Step 2: Configure the .env File

Create a file named `.env` in the root of the project by copying the example:

```bash
cp .env.example .env
```

Open `.env` in a text editor and enter your Gemini API key:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

---

## Step 3: Run Locally

Start the FastAPI application server locally:

```bash
uv run python app/api/main.py
```

The server will start up. Open your browser and navigate to:
[http://localhost:8000](http://localhost:8000)

- Use **Home / Analyze Soil** to upload soil photos.
- Use **Farmer Assistant** to chat with the AI.
- Use **Analysis History** to view past reports.

---

## Step 4: Deploy to Google Cloud Run

To host your application on Google Cloud Run, follow these steps:

1. **Log in to Google Cloud**:
   ```bash
   gcloud auth login
   ```

2. **Set your Google Cloud Project ID**:
   ```bash
   gcloud config set project <your-gcp-project-id>
   ```

3. **Deploy using the Agents CLI**:
   ```bash
   agents-cli deploy
   ```
   *Note: This command requires human confirmation. Follow the prompts in your terminal to complete the build and deploy.*
