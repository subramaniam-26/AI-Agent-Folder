import logging
import re

# Setup audit logger
logger = logging.getLogger("audit_logger")
logger.setLevel(logging.INFO)

# Make sure we don't duplicate handlers if script is reloaded
if not logger.handlers:
    # Print to console/stdout
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("[AUDIT] %(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(sh)

    # Store to local file in workspace
    try:
        fh = logging.FileHandler("audit.log", mode="a")
        fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)
    except Exception:
        pass

def log_audit(action: str, status: str, details: str):
    """Log structured security audit record."""
    message = f"Action: {action} | Status: {status} | Details: {details}"
    logger.info(message)

def validate_image_file(file_content: bytes) -> tuple[bool, str]:
    """Validates file signature (magic bytes) to ensure it is JPEG, PNG, or WEBP, and checks size."""
    file_size = len(file_content)
    max_size = 10 * 1024 * 1024  # 10MB

    if file_size > max_size:
        log_audit("file_size_validation", "REJECT", f"File size {file_size} exceeds 10MB limit")
        return False, "File size exceeds the maximum limit of 10MB."

    # Validate image magic bytes
    if file_content.startswith(b"\xff\xd8\xff"):
        log_audit("file_type_validation", "PASS", "JPEG signature matched")
        return True, "image/jpeg"
    elif file_content.startswith(b"\x89PNG\r\n\x1a\n"):
        log_audit("file_type_validation", "PASS", "PNG signature matched")
        return True, "image/png"
    elif file_content.startswith(b"RIFF") and b"WEBP" in file_content[8:15]:
        log_audit("file_type_validation", "PASS", "WEBP signature matched")
        return True, "image/webp"

    log_audit("file_type_validation", "REJECT", "Magic bytes do not match JPEG, PNG, or WEBP")
    return False, "Unsupported file format. Only JPEG, PNG, and WEBP images are allowed."

def detect_prompt_injection(user_input: str) -> tuple[bool, str]:
    """Detects potential prompt injection attempts in text input."""
    # List of common prompt injection patterns
    patterns = [
        r"ignore\s+(?:all\s+)?previous\s+instructions",
        r"system\s+prompt",
        r"override\s+instructions",
        r"you\s+are\s+now\s+a",
        r"act\s+as\s+a",
        r"forget\s+what\s+you\s+were\s+told",
        r"developer\s+mode",
        r"do\s+anything\s+now",
        r"dan\s+mode"
    ]

    for pattern in patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            log_audit("prompt_injection_check", "REJECT", f"Matched prompt injection pattern: {pattern}")
            return True, "Potential prompt injection detected. Request rejected."

    log_audit("prompt_injection_check", "PASS", "No prompt injection patterns matched")
    return False, ""

def sanitize_input_text(user_input: str) -> str:
    """Sanitizes input text by removing HTML tags and stripping whitespace."""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]*>", "", user_input)
    # Strip leading/trailing whitespaces
    cleaned = cleaned.strip()
    return cleaned

def enforce_mcp_access_control(tool_name: str) -> tuple[bool, str]:
    """Enforces MCP tool access control.

    Only allows access to soil-server, crop-server, and fertilizer-server tools.
    """
    allowed_tools = {
        "get_soil_statistics",
        "get_soil_health_score",
        "get_soil_profile",
        "get_crop_recommendation",
        "get_crop_profile",
        "get_fertilizer_recommendation",
        "get_fertilizer_profile",
        "analyze_multimodal_soil",
    }

    if tool_name in allowed_tools:
        log_audit("mcp_access_control", "PASS", f"Access granted to tool: {tool_name}")
        return True, ""

    log_audit("mcp_access_control", "REJECT", f"Access denied to unauthorized tool: {tool_name}")
    return False, f"Unauthorized tool access attempt: '{tool_name}'."
