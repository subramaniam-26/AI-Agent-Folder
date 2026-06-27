# Security Policy - SoilSense AI

This document summarizes the safety and security measures implemented in SoilSense AI to protect user data and ensure secure AI agent behavior.

---

## Prompt Injection Protection

All incoming parameters are validated before execution inside the tool call pipeline (`app/security.py`).
- **Callbacks**: A `before_tool_callback` intercepts MCP tool arguments.
- **Detection**: Standard prompts are scanned for injection keywords (such as "ignore previous instructions"). If detected, the request is instantly rejected with an error message.

---

## Input Validation

We utilize **Pydantic schemas** in FastAPI (`app/api/main.py`) to validate all requests (e.g. `ChatRequest` and `PdfReportRequest`). This prevents buffer overflows, malformed payloads, and injection attacks.

---

## Image Validation

Uploaded files undergo validation in `app/skills/image_validation.py` before they are processed by the multimodal server:
- Checks the file extension (must be a valid image type like `.jpg`, `.png`).
- Checks image header integrity using PIL (Python Imaging Library) to prevent arbitrary binary code execution.

---

## MCP Access Control

MCP servers run under restricted parameters inside local sandboxes:
- Unused/unauthorized sub-agent functions (like transferring state to external modules) are locked down and blocked using audit log access controls.

---

## Logging & Auditing

The system maintains real-time logs:
- **`audit.log`**: Records all tool calls, security exceptions, and blocked prompt injections.
- **FastAPI Logs**: Provides console tracebacks for HTTP request failures to facilitate quick auditing of runtime issues.
