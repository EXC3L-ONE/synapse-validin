import pytest
from .test_base import ValidinTestBase, CYAN, BLUE, YELLOW, GREEN, MAGENTA, RESET


class TestValidinWhois(ValidinTestBase):
    """Test Validin domain registration history"""

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
                    f"  {MAGENTA}created:{RESET} [{created_time}]  {format_time(created_time)}"
                )

            # Optional properties
            if node.get("updated"):
                updated_time = node.get("updated")
                print(
                    f"  {MAGENTA}updated:{RESET} [{updated_time}]  {format_time(updated_time)}"
                )
            if node.get("registrar"):
                print(f"  {MAGENTA}registrar:{RESET} {node.get('registrar')}")
            if node.get("expires"):
                expires_time = node.get("expires")
                print(
                    f"  {MAGENTA}expires:{RESET} [{expires_time}]  {format_time(expires_time)}"
                )

            print(f"\n{GREEN}=== Domain Registration Testing Complete ==={RESET}\n")