# Synapse-Validin

This Synapse Rapid Power-up adds support for ingesting [Validin](https://validin.com) enrichment data for IPv4 and FQDN nodes, plus project management capabilities.

## Installation

The easiest way to use this Power-Up is to load the JSON package into the Cortex by running: 

```bash
pkg.load --raw "https://raw.githubusercontent.com/EXC3L-ONE/synapse-validin/main/synapse_validin.json"
```

Alternatively, you can also clone this repo, and load the package via `python -m synapse.tools.genpkg` (see reference in Synapse docs [here](https://synapse.docs.vertex.link/en/latest/synapse/devguides/power-ups.html#dev-rapid-power-ups-build))

## Usage

### Initial Setup
```storm
ex.validin.setup.apikey <key> [--self]      # Set API key (globally or per-user)
ex.validin.setup.apihostname <hostname>     # Set API hostname
ex.validin.setup.tagprefix <prefix>         # Set tag prefix (default: rep.validin)
```

### Enrichment Commands
```storm
(inet:fqdn, inet:ipv4) | ex.validin.pdns [--include-extra]   # pDNS data (A/AAAA or all types)
inet:fqdn | ex.validin.whois                                 # Registration history  
inet:fqdn | ex.validin.host.subdomains                       # Subdomain discovery
(inet:fqdn, inet:ipv4) | ex.validin.host.responses           # HTTP crawl data
```

### Project Workflow

**1. Import projects from Validin:**
```storm
ex.validin.project.list --yield             # Creates proj:project nodes in Synapse
```

**2. Set active project:**
```storm
ex.validin.project.set <project_guid>       # Set global active project
# Now indicators use: $lib.globals.get("validin:active_project")
```

**3. Manage indicators with active project:**
```storm
# Pull indicators from active project
proj:project | ex.validin.project.indicators.get --yield

# Add indicators to active project (no GUID needed)
inet:fqdn=example.com | ex.validin.project.indicators.add $lib.globals.get("validin:active_project")

# Or specify project directly
inet:fqdn=example.com | ex.validin.project.indicators.add <project_guid>
```

**4. Sync projects:**
```storm
ex.validin.project.sync --mode pull         # Pull indicators from Validin projects
ex.validin.project.sync --mode push         # Push indicators to Validin
ex.validin.project.sync --mode draft        # Preview sync operations
```

### Optic UI Actions

Right-click on nodes in Optic for quick actions:
- **Domains/IPs**: pDNS, host responses, subdomains, whois
- **Indicators**: Add/remove from active project
- **Projects**: Set as active, get indicators

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
```bash
VALIDIN_API_KEY=your_api_key_here
TEST_PROJECT_GUID=your_project_guid
TEST_PROJECT_NAME=your_project_name
```

4. In `ex.validin.privsep.storm` - you'll need to set the HTTP request in `func makeValidinAPIRequest()` to `ssl_verify=$lib.false` in order for the Synapse test core to connect out to Validin (WIP to figure out a better solution)

5. Run tests:
```bash
python3 -m pytest test/
```