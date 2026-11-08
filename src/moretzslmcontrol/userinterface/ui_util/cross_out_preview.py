"""Preview-only inactive-state overlay; never modifies SLM output data."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageDraw, ImageFont


def disabled_preview(preview_bytes: NDArray[np.uint8]) -> NDArray[np.uint8]:
    height, width = preview_bytes.shape
    source = Image.fromarray(preview_bytes).convert('RGBA')
    overlay = Image.new('RGBA', source.size)
    painter = ImageDraw.Draw(overlay)
    font = ImageFont.load_default(size=max(8, min(height // 3, width // 5, 18)))
    bounds = painter.textbbox((0, 0), 'Off', font=font)
    text_width, text_height = bounds[2]-bounds[0], bounds[3]-bounds[1]
    left, top = (width-text_width)//2, (height-text_height)//2
    painter.rectangle((left-4, top-3, left+text_width+4, top+text_height+3), fill=(255, 255, 255, 190))
    painter.text((left-bounds[0], top-bounds[1]), 'Off', font=font, fill=(0, 0, 0, 235))
    return np.array(Image.alpha_composite(source, overlay).convert('L'), dtype=np.uint8)


# Preserve the old internal import for downstream users, with the new visual semantics.
cross_out_preview = disabled_preview
