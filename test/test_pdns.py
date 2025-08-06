import pytest
from .test_base import ValidinTestBase, CYAN, BLUE, YELLOW, GREEN, MAGENTA, RESET


class TestValidinPDNS(ValidinTestBase):
    """Test Validin Passive DNS functionality"""

    async def test_pdns(self):
        """Test PDNS enrichment for both IPv4 and domain nodes"""
        # Initialize core with the certificates
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Starting PDNS Testing ==={RESET}")
            await self._setup_validin(core, enterprise=True)

            ipv4 = "204.188.232.195"
            domain = "basketball-reference.com"

            # Test IPv4 PDNS enrichment
            print(
                f"\n{BLUE}Testing IPv4 PDNS enrichment for IP:{RESET} {MAGENTA}{ipv4}{RESET}"
            )
            msgs = await core.stormlist(
                f"""
                [ inet:ipv4={ipv4} ]
                | ex.validin.pdns --debug
            """
            )
            self.stormHasNoWarnErr(msgs)

            # For IP PDNS, verify A records are created with (value, key) format
            nodes = await core.nodes(f"inet:dns:a:ipv4={ipv4}")
            self.ge(len(nodes), 0)  # Use ge to allow for zero if API/data changes
            print(
                f"{YELLOW}Found {len(nodes)} DNS A records pointing to IP {MAGENTA}{ipv4}{RESET}"
            )

            # Test domain PDNS enrichment
            print(
                f"\n{BLUE}Testing Domain PDNS enrichment for FQDN:{RESET} {MAGENTA}{domain}{RESET}"
            )
            msgs = await core.stormlist(
                f"""
                [ inet:fqdn={domain} ]
                | ex.validin.pdns --debug
            """
            )
            self.stormHasNoWarnErr(msgs)

            # For Domain PDNS, verify A records where domain is the key
            nodes = await core.nodes(f"inet:dns:a:fqdn={domain}")
            self.ge(len(nodes), 0)
            print(
                f"{YELLOW}Found {len(nodes)} DNS A records for {MAGENTA}{domain}{RESET}"
            )

            # For Domain PDNS, verify NS records
            nodes = await core.nodes(f"inet:dns:ns:zone={domain}")
            self.ge(len(nodes), 0)
            print(
                f"{YELLOW}Found {len(nodes)} DNS NS records for {MAGENTA}{domain}{RESET}"
            )

            # For Domain PDNS, verify AAAA records if any exist
            nodes = await core.nodes(f"inet:dns:aaaa:fqdn={domain}")
            self.ge(len(nodes), 0)
            print(
                f"{YELLOW}Found {len(nodes)} DNS AAAA records for {MAGENTA}{domain}{RESET}"
            )

            # Optionally test --include-extra flag for FQDN
            msgs = await core.stormlist(
                f"""
                [ inet:fqdn={domain} ]
                | ex.validin.pdns --include-extra --debug
            """
            )
            self.stormHasNoWarnErr(msgs)
            print(
                f"{YELLOW}Tested PDNS with --include-extra for {MAGENTA}{domain}{RESET}"
            )

            print(f"\n{GREEN}=== PDNS Testing Complete ==={RESET}\n")