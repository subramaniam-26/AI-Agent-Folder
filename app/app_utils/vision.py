# app/app_utils/vision.py
"""Vision utilities for multimodal soil analysis.

This module provides lazy loading of a ResNet18 feature extractor and a helper
function to extract a fixed-size feature vector from an image file. The model is
loaded once on first use to avoid unnecessary startup overhead.

The implementation avoids downloading pretrained weights at runtime so the MCP
server remains stable in offline or sandboxed environments. If a trained soil
vision model is added later, replace the `MODEL_NAME` constant and adjust the
`load_vision_model` function accordingly.
"""

from __future__ import annotations

import pathlib
from typing import Final

import torch
from PIL import Image
from torchvision import models, transforms

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL_NAME: Final[str] = "resnet18"
DEVICE: Final[torch.device] = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Lazy-loaded singleton
_vision_model: None | torch.nn.Module = None

# Image preprocessing - uses the standard ResNet input shape and normalization.
_PREPROCESS = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def load_vision_model() -> torch.nn.Module:
    """Load (or retrieve) the local vision feature extractor.

    Returns
    -------
    torch.nn.Module
        The model with the final classification head removed, exposing a
        512-dimensional feature vector (ResNet18).
    """
    global _vision_model
    if _vision_model is None:
        model_factory = getattr(models, MODEL_NAME)
        try:
            base_model = model_factory(weights=None)
        except TypeError:
            base_model = model_factory(pretrained=False)

        # `fc` is the final linear layer; replace with identity to get features.
        base_model.fc = torch.nn.Identity()
        base_model.to(DEVICE)
        base_model.eval()
        _vision_model = base_model
    return _vision_model


def extract_image_features(image_path: str | pathlib.Path) -> torch.Tensor:
    """Extract a fixed-size (512-dim) feature tensor from an image file.

    Parameters
    ----------
    image_path: str | pathlib.Path
        Path to the input image (any format supported by Pillow).

    Returns
    -------
    torch.Tensor
        A 1-D tensor on the same device as the model, dtype ``torch.float32``.
    """
    img = Image.open(image_path).convert("RGB")
    tensor = _PREPROCESS(img).unsqueeze(0).to(DEVICE)  # shape: (1, 3, 224, 224)
    model = load_vision_model()
    with torch.no_grad():
        features = model(tensor)  # shape: (1, 512)
    return features.squeeze(0)  # shape: (512,)
