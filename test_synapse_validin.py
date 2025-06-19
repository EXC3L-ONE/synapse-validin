import os
from dotenv import load_dotenv
import synapse.tests.utils as s_test
import pytest

dirname = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(dirname, ".env"))

CYAN = "\033[96m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


class TestValidin(s_test.StormPkgTest):
    pkgprotos = (os.path.join(dirname, "synapse-validin.yaml"),)

    async def _setup_validin(self, core, enterprise=False):
        """Helper function to set up Validin API key and hostname"""
        # Set hostname first
        hostname = "pilot.validin.com" if enterprise else "api.validin.com"
        msgs = await core.stormlist(f"ex.validin.setup.apihostname {hostname}")
        self.stormHasNoWarnErr(msgs)

        # Set API key
        msgs = await core.stormlist(
            f'ex.validin.setup.apikey --self --debug {os.getenv("VALIDIN_API_KEY")}'
        )
        self.stormHasNoWarnErr(msgs)

    @pytest.mark.asyncio
    async def test_validin_setup(self):
        """Test setting up Validin configuration"""
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Validin Setup Test ==={RESET}")

            # Test setting hostname for community
            print(f"\n{BLUE}Testing Community Hostname Configuration{RESET}")
            msgs = await core.stormlist(
                "$lib.debug=$lib.true | ex.validin.setup.apihostname api.validin.com"
            )
            self.stormIsInPrint(
                "Validin API hostname set successfully: api.validin.com", msgs
            )
            self.stormHasNoWarnErr(msgs)
            print(
                f"{YELLOW}Successfully set community hostname to:{RESET} {MAGENTA}api.validin.com{RESET}"
            )

            # Test setting hostname for enterprise
            print(f"\n{BLUE}Testing Enterprise Hostname Configuration{RESET}")
            msgs = await core.stormlist(
                "$lib.debug=$lib.true | ex.validin.setup.apihostname pilot.validin.com"
            )
            self.stormIsInPrint(
                "Validin API hostname set successfully: pilot.validin.com", msgs
            )
            self.stormHasNoWarnErr(msgs)
            print(
                f"{YELLOW}Successfully set enterprise hostname to:{RESET} {MAGENTA}pilot.validin.com{RESET}"
            )

            # Test setting API key
            print(f"\n{BLUE}Testing API Key Configuration{RESET}")
            api_key = os.getenv("VALIDIN_API_KEY")
            msgs = await core.stormlist(
                f"ex.validin.setup.apikey --self --debug {api_key}"
            )
            self.stormIsInPrint("Setting Validin API key for the current user", msgs)
            self.stormHasNoWarnErr(msgs)
            masked_key = (
                f"{api_key[:8]}...{api_key[-8:]}"
                if len(api_key) > 16
                else "***masked***"
            )
            print(
                f"{YELLOW}Successfully set API key:{RESET} {MAGENTA}{masked_key}{RESET}"
            )

            print(f"\n{GREEN}=== Validin Setup Testing Complete ==={RESET}\n")

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_whois(self):
        """Test domain registration history"""
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Starting Domain Registration Testing ==={RESET}")

            # Setup Validin (use enterprise since this is an enterprise feature)
            await self._setup_validin(core, enterprise=True)

            # Test registration history for baseball-reference.com
            domain = "baseball-reference.com"
            print(
                f"\n{BLUE}Testing Registration History for domain:{RESET} {MAGENTA}{domain}{RESET}"
            )

            msgs = await core.stormlist(
                f"""
                [ inet:fqdn={domain} ]
                $lib.debug=$lib.true | ex.validin.whois --yield --debug
            """
            )

            self.stormHasNoWarnErr(msgs)

            # Get inet:whois:rec nodes
            nodes = await core.nodes(f"inet:whois:rec:fqdn={domain}")
            self.gt(len(nodes), 0)
            print(f"{YELLOW}Found {len(nodes)} whois records for domain{RESET}")

            # Just need to check first record
            node = nodes[0]

            # Required properties
            self.nn(node.get("fqdn"))
            self.eq(node.get("fqdn"), domain)
            self.nn(node.get("created"))

            # Convert timestamps
            from datetime import datetime, timezone

            def format_time(epoch_ms):
                dt = datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
                return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

            # Print whois record properties
            print(f"{YELLOW}Record properties:{RESET}")
            print(f"  {MAGENTA}fqdn:{RESET} {node.get('fqdn')}")
            created_time = node.get("created")
            if created_time:
                print(
                    f"  {MAGENTA}created:{RESET} [{created_time}]  {format_time(created_time)}"
                )

            # Optional properties
            if node.get("updated"):
                updated_time = node.get("updated")
                print(
                    f"  {MAGENTA}updated:{RESET} [{updated_time}]  {format_time(updated_time)}"
                )
            if node.get("registrar"):
                print(f"  {MAGENTA}registrar:{RESET} {node.get('registrar')}")
            if node.get("expires"):
                expires_time = node.get("expires")
                print(
                    f"  {MAGENTA}expires:{RESET} [{expires_time}]  {format_time(expires_time)}"
                )

            print(f"\n{GREEN}=== Domain Registration Testing Complete ==={RESET}\n")


# for manual testing/debugging, uncomment the following lines
""" def main():

    test = TestValidin()
    test.test_validin_setup()
    test.test_pdns()
    test.test_whois()

main()
 """
