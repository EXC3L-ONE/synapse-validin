# Synapse-Validin
This Synapse Rapid Power-up adds support for ingesting [Validin](https://validin.com) enrichment data for IPv4 and FQDN nodes.

---
## Usage
There are XYZ commands available: 
- `ex.validin.pdns`
    - Enrich inbound `inet:ipv4` or `inet:fqdn` nodes with pDNS
- `ex.validin.setup.apikey`
    - Setup Validin API key
- `ex.validin.setup.tagprefix`
    - Setup Validin tag prefix

---
## Installation
The easiest way to use this Power-Up is to load the JSON package into the Cortex by running: 

`pkg.load --raw "https://raw.githubusercontent.com/EXC3L-ONE/synapse-validin/main/synapse_validin.json"`

Alternatively, you can also clone this repo, and load the package via `python -m synapse.tools.genpkg` (see reference in Synapse docs [here](https://synapse.docs.vertex.link/en/latest/synapse/userguides/syn_tools_genpkg.html#building-the-example-package))

---
### Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your environment:
```bash
cp env.example .env
```

3. Edit `.env` and add your Validin API key:
```
VALIDIN_API_KEY=your_api_key_here
```

4. In `ex.validin.privsep.storm` - you'll need to set the HTTP request in `func makeValidinAPIRequest()` to `ssl_verify=$lib.false` in order for the Synapse test core to connect out to Validin (WIP to figure out a better solution)

5. Run tests
```python
python3 -m pytest -svx test_synapse_validin.py
```