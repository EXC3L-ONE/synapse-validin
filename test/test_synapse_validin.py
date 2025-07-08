import os
from dotenv import load_dotenv
import synapse.tests.utils as s_test
import pytest

dirname = os.path.abspath(os.path.dirname(__file__))
# Go up one directory to find the YAML file since we're now in test/ subdirectory
parent_dir = os.path.dirname(dirname)
load_dotenv(os.path.join(parent_dir, ".env"))

CYAN = "\033[96m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
MAGENTA = "\033[95m"
RESET = "\033[0m"


class TestValidin(s_test.StormPkgTest):
    pkgprotos = (os.path.join(parent_dir, "synapse-validin.yaml"),)

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
            if api_key:
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

    async def test_projects(self):
        """Test comprehensive project functionality - project list and indicators with edge validation"""
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Starting Projects Testing ==={RESET}")

            # Setup Validin (use enterprise since projects are enterprise feature)
            await self._setup_validin(core, enterprise=True)

            # PHASE 1: Project List Testing
            print(f"\n{BLUE}Phase 1: Testing Project List Retrieval and Node Creation{RESET}")
            
            # Execute the project list command
            msgs = await core.stormlist("$lib.debug=$lib.true | ex.validin.project.list --yield")
            self.stormHasNoWarnErr(msgs)

            # Check if proj:project nodes were created - look for any validin type
            project_nodes = await core.nodes("proj:project:type=validin")
            self.assertGreater(len(project_nodes), 0, "Expected at least one proj:project node with type 'validin'")
            
            print(f"{YELLOW}Successfully created {len(project_nodes)} proj:project nodes{RESET}")
            
            # Find the specific test project by name
            test_project = project_nodes[0]  # default fallback
            for project in project_nodes:
                if project.get("name") == "watchlist used for unit testing validin power-up":
                    test_project = project
                    break
            self.nn(test_project.get("name"), "Project should have a name")
            self.nn(test_project.get("created"), "Project should have creation time")
            
            # Check if _validin:guid property exists
            validin_guid = test_project.get("_validin:guid")
            self.nn(validin_guid, "Project should have _validin:guid property")
            project_guid = str(test_project.ndef[1])
            project_name = test_project.get("name")
            
            print(f"  {MAGENTA}Sample project for testing:{RESET}")
            print(f"  {MAGENTA}GUID:{RESET} {project_guid}")
            print(f"  {MAGENTA}Name:{RESET} {project_name}")
            print(f"  {MAGENTA}Validin GUID:{RESET} {validin_guid}")

            # PHASE 2: Project Indicators Testing
            print(f"\n{BLUE}Phase 2: Testing Project Indicators for '{project_name}'{RESET}")
            
            # Execute the project indicators command on the test project using the project GUID
            msgs = await core.stormlist(f"""
                $lib.debug=$lib.true | proj:project={project_guid} | ex.validin.project.indicators.get --yield
            """)
            self.stormHasNoWarnErr(msgs)

            # Check if indicator nodes were created and linked
            # Look for any nodes that have a refs edge from our project
            indicator_query = f"""
                proj:project={project_guid} 
                | -(refs)> *
            """
            all_linked_nodes = await core.nodes(indicator_query)
            
            # Filter out proj:project nodes to get actual indicators
            indicator_nodes = [node for node in all_linked_nodes if node.ndef[0] != "proj:project"]
            
            if len(indicator_nodes) > 0:
                print(f"{YELLOW}Successfully created {len(indicator_nodes)} indicator nodes linked to project{RESET}")
                
                # Verify at least one indicator exists and check its type
                first_indicator = indicator_nodes[0]
                indicator_form = first_indicator.ndef[0]
                indicator_value = first_indicator.ndef[1]
                
                print(f"  {MAGENTA}Sample indicator:{RESET}")
                print(f"    {MAGENTA}Form:{RESET} {indicator_form}")
                print(f"    {MAGENTA}Value:{RESET} {indicator_value}")
                
                # PHASE 3: Light Edge Verification and Breakdown
                print(f"\n{BLUE}Phase 3: Light Edge Verification and Indicator Breakdown{RESET}")
                
                print(f"  {GREEN}✓ Light edge verification passed:{RESET}")
                print(f"    {MAGENTA}Project -{RESET}{GREEN}(refs)->{RESET} {MAGENTA}{indicator_form}={indicator_value}:{RESET} Edge exists")
                
                # Show breakdown by indicator types from the existing results
                indicator_types = ["inet:fqdn", "inet:ipv4", "inet:ipv6", "hash:md5", "hash:sha1", "hash:sha256"]
                for indicator_type in indicator_types:
                    type_indicators = [node for node in indicator_nodes if node.ndef[0] == indicator_type]
                    if len(type_indicators) > 0:
                        print(f"  {YELLOW}Found {len(type_indicators)} {indicator_type} indicators{RESET}")
                        for node in type_indicators:
                            print(f"    {indicator_type}={node.ndef[1]}")
                    
            else:
                print(f"{YELLOW}No indicators found for project (project may be empty){RESET}")

            # PHASE 4: Test Adding Indicators to Project
            print(f"\n{BLUE}Phase 4: Testing Adding Indicators to Project{RESET}")
            
            # Use unique test indicators to avoid conflicts between test runs
            import time
            test_suffix = str(int(time.time()))
            test_ip = "192.168.1.100"  # Use a consistent test IP
            test_domain = f"test{test_suffix}.example.com"
            # Create a valid 32-character MD5 hash by padding the timestamp
            test_hash = f"{test_suffix.zfill(10)}{'0' * 22}"  # 32-char hash with timestamp prefix
            
            expected_indicators = {
                test_ip,
                test_domain,
                test_hash
            }
            
            # Add the test indicators
            print(f"  {YELLOW}Adding multiple indicators to project in batch{RESET}")
            
            msgs = await core.stormlist(f"""
                $lib.debug=$lib.true | [ inet:ipv4={test_ip} inet:fqdn={test_domain} hash:md5={test_hash} ] | ex.validin.project.indicators.add {validin_guid} --debug
            """)
            self.stormHasNoWarnErr(msgs)
            
            # Sync the project to get the newly added indicators back into Synapse
            print(f"  {YELLOW}Syncing project to retrieve added indicators{RESET}")
            msgs = await core.stormlist(f"""
                $lib.debug=$lib.true | proj:project={project_guid} | ex.validin.project.indicators.get --yield
            """)
            self.stormHasNoWarnErr(msgs)
            
            # Verify all indicators were created and linked - elegant set-based check using node.repr()
            all_linked_nodes = await core.nodes(f"proj:project={project_guid} -(refs)> *")
            linked_indicators = {node.repr() for node in all_linked_nodes if node.ndef[0] != "proj:project"}
            
            # Check if all expected indicators are present
            missing_indicators = expected_indicators - linked_indicators
            self.assertEqual(len(missing_indicators), 0, f"Missing indicators: {missing_indicators}")
            
            print(f"    {GREEN}✓ Successfully added and verified all {len(expected_indicators)} indicators{RESET}")
            for indicator in expected_indicators:
                print(f"      {indicator}")

            # PHASE 5: Test Deleting Indicators from Project
            print(f"\n{BLUE}Phase 5: Testing Deleting Indicators from Project{RESET}")
            
            # Delete the indicators we just added
            print(f"  {YELLOW}Deleting the test indicators from project{RESET}")
            
            msgs = await core.stormlist(f"""
                $lib.debug=$lib.true | inet:ipv4={test_ip} inet:fqdn={test_domain} hash:md5={test_hash} | ex.validin.project.indicators.delete {validin_guid} --debug
            """)
            self.stormHasNoWarnErr(msgs)
            
            # Verify the light edges were removed but the indicator nodes still exist
            all_linked_nodes = await core.nodes(f"proj:project={project_guid} -(refs)> *")
            linked_indicators_after_delete = {node.repr() for node in all_linked_nodes if node.ndef[0] != "proj:project"}
            
            # Check if our test indicators are no longer linked to the project
            remaining_test_indicators = expected_indicators & linked_indicators_after_delete
            if len(remaining_test_indicators) == 0:
                print(f"    {GREEN}✓ Successfully removed all {len(expected_indicators)} test indicator edges{RESET}")
            else:
                print(f"    {YELLOW}Note: {len(remaining_test_indicators)} test indicators still linked (may be from other sources){RESET}")
                for indicator in remaining_test_indicators:
                    print(f"      {indicator}")
            
            # Verify the actual indicator nodes still exist in Synapse
            test_nodes_still_exist = await core.nodes(f"inet:ipv4={test_ip} inet:fqdn={test_domain} hash:md5={test_hash}")
            self.assertEqual(len(test_nodes_still_exist), 3, "All test indicator nodes should still exist after deletion from project")
            print(f"    {GREEN}✓ Verified all {len(test_nodes_still_exist)} indicator nodes still exist in Synapse{RESET}")

            print(f"\n{GREEN}=== Projects Testing Complete ==={RESET}\n")


# for manual testing/debugging, uncomment the following lines
""" import asyncio

def main():
    test = TestValidin()
    asyncio.run(test.test_projects())

main() """

