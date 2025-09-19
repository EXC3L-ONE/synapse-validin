# Synapse-Validin
This Synapse Rapid Power-up provides comprehensive [Validin](https://validin.com) integration for passive DNS, domain reputation, WHOIS history, threat intelligence, and advanced host search capabilities.

---
## Usage

### Setup Commands
- `ex.validin.setup.apikey` - Configure Validin API authentication
- `ex.validin.setup.tagprefix` - Set tag prefix for Validin enrichment tags
- `ex.validin.setup.apihostname` - Configure API hostname for custom deployments

### Enrichment Commands
- `ex.validin.pdns` - Retrieve passive DNS records for IPs and domains
- `ex.validin.whois` - Get domain registration history
- `ex.validin.host.subdomains` - Discover subdomains for domains
- `ex.validin.host.responses` - Get HTTP crawl history for hosts
- `ex.validin.host.search` - Execute advanced search queries
- `ex.validin.domain.reputation` - Get domain reputation scores and risk tags

### Project Management
- `ex.validin.project.list` - List accessible Validin projects
- `ex.validin.project.indicators.get` - Retrieve project indicators
- `ex.validin.project.indicators.add` - Add indicators to projects
- `ex.validin.project.indicators.delete` - Remove indicators from projects

### Threat Intelligence
- `ex.validin.threat.group.indicators` - Import threat group IOCs with campaign tags

---
## Installation
The easiest way to use this Power-Up is to load the JSON package into the Cortex by running:

`pkg.load --raw "https://raw.githubusercontent.com/EXC3L-ONE/synapse-validin/main/synapse_validin.json"`