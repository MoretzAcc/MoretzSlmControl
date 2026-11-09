# Moretz SLM Control Client

Python client for controlling a Moretz SLM Control instance through HEROS.


Using pip or conda:
```bash
python -m pip install "git+https://github.com/MoretzAcc/MoretzSlmControl.git#subdirectory=client"
```

Using uv:
```bash
uv add "git+https://github.com/MoretzAcc/MoretzSlmControl.git#subdirectory=client"
```

### Example

A full example can be found in the `examples` directory.

To apply a hologram pattern to the SLM:

```python
from moretzslmclient import SlmHeroApi

hologram: NDArray[np.float32] = ... # Your hologram pattern

hero_name = "slm_12345678__example_name"

with SlmHeroApi(hero_name) as slm:
    slm.setHologramPattern(hologram)
```


## Remote optical parameters

Zernike setters also synchronize the corresponding coefficient fields in the desktop UI.
Modification setters use the same units as the UI: X/Y/Z and pixel pitch in micrometers,
wavelength in nanometers, focal length in millimeters, and unitless magnification.

```python
with SlmHeroApi(hero_name) as slm:
    slm.setZernikeAstigmatism0(0.2)
    slm.setModificationWavelength(780)
    slm.setModificationFocalLength(20)
    slm.setModificationMagnification(2)
    slm.setModificationPixelPitch(8)
    slm.setModificationX(1500)
    slm.setModificationY(-250)
    slm.setModificationZ(10)
```

Each setter recalculates the modification pattern using the other current parameters.
The UI automatically increases its slider range to include remotely supplied shifts;
smaller shifts do not shrink it. Slider max shift has no HEROS setter.

## Bounded notebook previews

```python
import numpy as np
from moretzslmclient import plotHologram

phase = np.zeros((2160, 3840), dtype=np.float32)
plotHologram(phase)  # Bounded to at most about one million preview pixels.
plotHologram(phase, max_preview_pixels=None)  # Explicit native sampling.
```

Preview sampling retains native coordinate extents and never changes the array sent to the SLM. Shared phase conversion and file helpers live in this package; it does not import the GUI/server. Discovery opens a scoped network observer only when requested. To install this fork's client, substitute `MoretzAccAi` for `MoretzAcc` in the Git URL, or run `uv sync --project client` from the checkout. The server's `uv sync` installs the matching local client automatically.
