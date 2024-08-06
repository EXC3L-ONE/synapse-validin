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
