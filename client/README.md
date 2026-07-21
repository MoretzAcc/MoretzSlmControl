# Moretz SLM Control Client

Python client for controlling a Moretz SLM Control instance through HEROS.


Using pip or conda:
```bash
python -m pip install "moretzslmclient @ git+https://github.com/MoretzAcc/MoretzSlmControl.git#subdirectory=client"
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

