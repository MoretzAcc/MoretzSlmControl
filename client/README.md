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


## Bounded notebook previews

```python
import numpy as np
from moretzslmclient import plotHologram

phase = np.zeros((2160, 3840), dtype=np.float32)
plotHologram(phase)  # Bounded to at most about one million preview pixels.
plotHologram(phase, max_preview_pixels=None)  # Explicit native sampling.
```

Preview sampling retains native coordinate extents and never changes the array sent to the SLM. Shared phase conversion and file helpers live in this package; it does not import the GUI/server. Discovery opens a scoped network observer only when requested. To install this fork's client, substitute `MoretzAccAi` for `MoretzAcc` in the Git URL, or run `uv sync --project client` from the checkout. The server's `uv sync` installs the matching local client automatically.
