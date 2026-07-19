# Moretz SLM Control Client

Python client for controlling a Moretz SLM Control instance through HEROS.

```bash
uv add --editable ../../MoretzSlmControl/client
```

```python
from moretzslmclient import SlmHeroApi

with SlmHeroApi("slmHero_example") as slm:
    slm.enableHologramPattern(True)
```
