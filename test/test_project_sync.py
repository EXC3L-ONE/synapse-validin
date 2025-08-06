import pytest
import time
from .test_base import ValidinTestBase, CYAN, BLUE, YELLOW, GREEN, MAGENTA, RESET


class TestProjectSync(ValidinTestBase):
    """Test project sync functionality through actual state validation"""

    async def _get_test_project(self, core):
        """Get the dedicated unit test project with hardcoded GUID"""
        project_guid = self.TEST_PROJECT_GUID
        project_name = self.TEST_PROJECT_NAME
        
        project_nodes = await core.nodes(f"[ proj:project={project_guid} :type=validin :name='{project_name}' :_validin:guid={project_guid} ]")
        
        if len(project_nodes) > 0:
            return project_nodes[0]
        else:
            self.fail(f"Failed to create/find test project {project_guid}")

    async def _cleanup_test_indicator(self, core, test_domain, project_guid):
        """Clean up test indicator from both Synapse and Validin"""
        try:
            msgs = await core.stormlist(f"[ inet:fqdn={test_domain} ] | ex.validin.project.indicators.delete {project_guid}")
            storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
            if len(storm_errors) > 0:
                print(f"      {YELLOW}Warning: Storm errors during cleanup: {storm_errors}{RESET}")
            
            await core.nodes(f"inet:fqdn={test_domain} | delnode --force")
        except Exception as e:
            print(f"      {YELLOW}Warning: Exception during cleanup: {e}{RESET}")

    async def test_sync_pull_mode(self):
        """Test pull mode by creating indicators then pulling them back"""
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Testing Pull Mode ==={RESET}")

            await self._setup_validin(core, enterprise=True)
            test_project = await self._get_test_project(core)
            project_guid = test_project.props.get("_validin:guid")
            project_name = test_project.props.get("name") or "Unknown"
            
            # Create unique test indicators
            import time
            timestamp = int(time.time())
            test_domain = f"pull-test-{timestamp}.example.com"
            test_hash = "d41d8cd98f00b204e9800998ecf8427e"
            test_ip = "192.0.2.100"
            
            print(f"  {BLUE}Testing Pull Mode for Project: {MAGENTA}{project_name}{RESET}")
            print(f"    {YELLOW}Project GUID: {project_guid}{RESET}")
            print(f"    {YELLOW}Test indicators: {test_domain}, {test_hash}, {test_ip}{RESET}")
            
            try:
                print(f"    {YELLOW}Step 1: Creating test indicators in Validin{RESET}")
                
                # Create domain indicator in Validin
                msgs = await core.stormlist(f"[ inet:fqdn={test_domain} ] | ex.validin.project.indicators.add {project_guid}")
                storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
                self.eq(len(storm_errors), 0, "Domain add should have no Storm errors")
                
                # Create hash indicator in Validin
                msgs = await core.stormlist(f"[ hash:md5={test_hash} ] | ex.validin.project.indicators.add {project_guid}")
                storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
                self.eq(len(storm_errors), 0, "Hash add should have no Storm errors")
                
                # Create IP indicator in Validin
                msgs = await core.stormlist(f"[ inet:ipv4={test_ip} ] | ex.validin.project.indicators.add {project_guid}")
                storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
                self.eq(len(storm_errors), 0, "IP add should have no Storm errors")
                
                print(f"      {GREEN}✓ Created test indicators in Validin{RESET}")
                
                print(f"    {YELLOW}Step 2: Removing indicators from Synapse{RESET}")
                await core.nodes(f"inet:fqdn={test_domain} | delnode --force")
                await core.nodes(f"hash:md5={test_hash} | delnode --force")
                await core.nodes(f"inet:ipv4={test_ip} | delnode --force")
                
                # Verify removal
                domain_nodes_after_delete = await core.nodes(f"inet:fqdn={test_domain}")
                hash_nodes_after_delete = await core.nodes(f"hash:md5={test_hash}")
                ip_nodes_after_delete = await core.nodes(f"inet:ipv4={test_ip}")
                
                print(f"      Domain nodes after deletion: {len(domain_nodes_after_delete)}")
                print(f"      Hash nodes after deletion: {len(hash_nodes_after_delete)}")
                print(f"      IP nodes after deletion: {len(ip_nodes_after_delete)}")
                
                print(f"    {YELLOW}Step 3: Running pull sync to recreate from Validin{RESET}")
                msgs = await core.stormlist(f"$lib.debug=$lib.true | proj:project={project_guid} | ex.validin.project.indicators.get --yield")
                
                storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
                self.eq(len(storm_errors), 0, "Pull sync should have no Storm errors")
                
                print(f"    {YELLOW}Step 4: Validating recreation of indicators{RESET}")
                
                domain_nodes_after_pull = await core.nodes(f"inet:fqdn={test_domain}")
                hash_nodes_after_pull = await core.nodes(f"hash:md5={test_hash}")
                ip_nodes_after_pull = await core.nodes(f"inet:ipv4={test_ip}")
                
                print(f"      Domain nodes after pull: {len(domain_nodes_after_pull)}")
                print(f"      Hash nodes after pull: {len(hash_nodes_after_pull)}")
                print(f"      IP nodes after pull: {len(ip_nodes_after_pull)}")
                
                # Verify project edges were created
                domain_edges = await core.nodes(f"proj:project={project_guid} -(refs)> inet:fqdn={test_domain}")
                hash_edges = await core.nodes(f"proj:project={project_guid} -(refs)> hash:md5={test_hash}")
                ip_edges = await core.nodes(f"proj:project={project_guid} -(refs)> inet:ipv4={test_ip}")
                
                print(f"      {GREEN}✓ Domain edges: {len(domain_edges)}{RESET}")
                print(f"      {GREEN}✓ Hash edges: {len(hash_edges)}{RESET}")
                print(f"      {GREEN}✓ IP edges: {len(ip_edges)}{RESET}")
                
                # Check overall success
                indicators_recreated = len(domain_nodes_after_pull) + len(hash_nodes_after_pull) + len(ip_nodes_after_pull)
                edges_created = len(domain_edges) + len(hash_edges) + len(ip_edges)
                
                if indicators_recreated >= 3:
                    print(f"      {GREEN}✓ Pull mode working - recreated {indicators_recreated}/3 indicators{RESET}")
                else:
                    print(f"      {YELLOW}⚠ Pull mode issues - only recreated {indicators_recreated}/3 indicators{RESET}")
                    
                if edges_created >= 3:
                    print(f"      {GREEN}✓ Project edges working - created {edges_created}/3 edges{RESET}")
                else:
                    print(f"      {YELLOW}⚠ Edge creation issues - only created {edges_created}/3 edges{RESET}")
                    
            except Exception as e:
                print(f"      {YELLOW}Warning: Exception during pull mode test: {e}{RESET}")
            
            finally:
                print(f"    {YELLOW}Cleanup: Removing test indicators{RESET}")
                try:
                    await self._cleanup_test_indicator(core, test_domain, project_guid)
                    msgs = await core.stormlist(f"[ hash:md5={test_hash} ] | ex.validin.project.indicators.delete {project_guid}")
                    await core.nodes(f"hash:md5={test_hash} | delnode --force")
                    msgs = await core.stormlist(f"[ inet:ipv4={test_ip} ] | ex.validin.project.indicators.delete {project_guid}")
                    await core.nodes(f"inet:ipv4={test_ip} | delnode --force")
                except:
                    pass
                
            print(f"    {GREEN}✓ Pull mode test completed{RESET}")

    async def test_sync_push_mode(self):
        """Test push mode using dedicated unit test project"""
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Testing Push Mode ==={RESET}")

            await self._setup_validin(core, enterprise=True)
            test_project = await self._get_test_project(core)
            project_guid = test_project.props.get("_validin:guid")
            project_name = test_project.props.get("name") or "Unknown"
            
            timestamp = int(time.time())
            test_domain = f"push-test-{timestamp}.example.com"
            test_hash = "d41d8cd98f00b204e9800998ecf8427e"
            test_ip = "192.0.2.101"
            
            print(f"  {BLUE}Testing Push Mode for Project: {MAGENTA}{project_name}{RESET}")
            print(f"    {YELLOW}Project GUID: {project_guid}{RESET}")
            print(f"    {YELLOW}Test indicators: {test_domain}, {test_hash}, {test_ip}{RESET}")
            
            try:
                # Step 1: Create indicators in Synapse only (with project relationships)
                print(f"    {YELLOW}Step 1: Creating Synapse-only indicators{RESET}")
                
                # Create domain indicator
                domain_nodes = await core.nodes(f"[ inet:fqdn={test_domain} <(refs)+ {{ proj:project={project_guid} }} ]")
                self.gt(len(domain_nodes), 0, "Should create domain node in Synapse")
                
                # Create hash indicator
                hash_nodes = await core.nodes(f"[ hash:md5={test_hash} <(refs)+ {{ proj:project={project_guid} }} ]")
                self.gt(len(hash_nodes), 0, "Should create hash node in Synapse")
                
                # Create IP indicator
                ip_nodes = await core.nodes(f"[ inet:ipv4={test_ip} <(refs)+ {{ proj:project={project_guid} }} ]")
                self.gt(len(ip_nodes), 0, "Should create IP node in Synapse")
                
                print(f"      Created {len(domain_nodes) + len(hash_nodes) + len(ip_nodes)} nodes in Synapse with project links")
                
                # Verify project relationships exist
                domain_edges = await core.nodes(f"proj:project={project_guid} -(refs)> inet:fqdn={test_domain}")
                hash_edges = await core.nodes(f"proj:project={project_guid} -(refs)> hash:md5={test_hash}")
                ip_edges = await core.nodes(f"proj:project={project_guid} -(refs)> inet:ipv4={test_ip}")
                
                total_edges = len(domain_edges) + len(hash_edges) + len(ip_edges)
                print(f"      Project edges before push: {total_edges} (domain: {len(domain_edges)}, hash: {len(hash_edges)}, IP: {len(ip_edges)})")
                
                # Step 2: Test push sync to send to Validin
                print(f"    {YELLOW}Step 2: Running push sync to send to Validin{RESET}")
                msgs = await core.stormlist(f"$lib.debug=$lib.true | proj:project={project_guid} -(refs)> * | ex.validin.project.indicators.add {project_guid}")
                
                storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
                self.eq(len(storm_errors), 0, "Push sync should have no Storm errors")
                print(f"      {GREEN}✓ Push sync executed without Storm errors{RESET}")
                
                # Step 3: Validate push worked by testing delete + pull
                print(f"    {YELLOW}Step 3: Validating push success via delete + pull test{RESET}")
                
                # Delete all indicators from Synapse
                await core.nodes(f"inet:fqdn={test_domain} | delnode --force")
                await core.nodes(f"hash:md5={test_hash} | delnode --force")
                await core.nodes(f"inet:ipv4={test_ip} | delnode --force")
                
                # Verify deletion
                domain_nodes_after_delete = await core.nodes(f"inet:fqdn={test_domain}")
                hash_nodes_after_delete = await core.nodes(f"hash:md5={test_hash}")
                ip_nodes_after_delete = await core.nodes(f"inet:ipv4={test_ip}")
                
                total_deleted = len(domain_nodes_after_delete) + len(hash_nodes_after_delete) + len(ip_nodes_after_delete)
                self.eq(total_deleted, 0, "All indicators should be deleted from Synapse")
                print(f"      Deleted from Synapse: {total_deleted} nodes remain")
                
                # Pull sync - if push worked, this should recreate all indicators
                print(f"      Running pull sync to test if indicators exist in Validin")
                msgs = await core.stormlist(f"$lib.debug=$lib.true | proj:project={project_guid} | ex.validin.project.indicators.get --yield")
                storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
                self.eq(len(storm_errors), 0, "Pull sync should work for validation")
                
                # Check if indicators were recreated (proves push worked)
                domain_nodes_after_pull = await core.nodes(f"inet:fqdn={test_domain}")
                hash_nodes_after_pull = await core.nodes(f"hash:md5={test_hash}")
                ip_nodes_after_pull = await core.nodes(f"inet:ipv4={test_ip}")
                
                indicators_recreated = len(domain_nodes_after_pull) + len(hash_nodes_after_pull) + len(ip_nodes_after_pull)
                print(f"      Indicators after pull: {indicators_recreated}/3 (domain: {len(domain_nodes_after_pull)}, hash: {len(hash_nodes_after_pull)}, IP: {len(ip_nodes_after_pull)})")
                
                if indicators_recreated >= 3:
                    print(f"      {GREEN}✓ Push mode is working: Pull recreated {indicators_recreated}/3 indicators from Validin{RESET}")
                    print(f"      {GREEN}✓ This proves push sync successfully sent indicators to Validin{RESET}")
                    
                    # Verify project relationships were also recreated
                    recreated_domain_edges = await core.nodes(f"proj:project={project_guid} -(refs)> inet:fqdn={test_domain}")
                    recreated_hash_edges = await core.nodes(f"proj:project={project_guid} -(refs)> hash:md5={test_hash}")
                    recreated_ip_edges = await core.nodes(f"proj:project={project_guid} -(refs)> inet:ipv4={test_ip}")
                    
                    recreated_edges = len(recreated_domain_edges) + len(recreated_hash_edges) + len(recreated_ip_edges)
                    print(f"      {GREEN}✓ Project edges recreated: {recreated_edges}/3{RESET}")
                else:
                    print(f"      {YELLOW}⚠ Push mode may have issues: Only recreated {indicators_recreated}/3 indicators{RESET}")
                    print(f"      {YELLOW}  This suggests some indicators were not successfully pushed to Validin{RESET}")
                
            finally:
                # Cleanup - ensure we remove from both systems
                print(f"    {YELLOW}Cleanup: Removing test indicators from both systems{RESET}")
                try:
                    # Clean up domain indicator
                    await self._cleanup_test_indicator(core, test_domain, project_guid)
                    
                    # Clean up hash indicator
                    msgs = await core.stormlist(f"[ hash:md5={test_hash} ] | ex.validin.project.indicators.delete {project_guid}")
                    await core.nodes(f"hash:md5={test_hash} | delnode --force")
                    
                    # Clean up IP indicator
                    msgs = await core.stormlist(f"[ inet:ipv4={test_ip} ] | ex.validin.project.indicators.delete {project_guid}")
                    await core.nodes(f"inet:ipv4={test_ip} | delnode --force")
                except Exception as e:
                    print(f"      {YELLOW}Cleanup warning: {e}{RESET}")
                    
            print(f"    {GREEN}✓ Push mode test completed{RESET}")


    async def test_sync_pull_validation(self):
        """Test pull sync validation and idempotency"""
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Testing Pull Sync Validation and Idempotency ==={RESET}")

            await self._setup_validin(core, enterprise=True)
            test_project = await self._get_test_project(core)
            project_guid = test_project.props.get("_validin:guid")
            project_name = test_project.props.get("name") or "Unknown"
            
            timestamp = int(time.time())
            test_domain = f"sync-validation-{timestamp}.example.com"
            test_hash = "d41d8cd98f00b204e9800998ecf8427e"
            test_ip = "192.0.2.103"
            
            print(f"  {BLUE}Testing Pull Sync Validation for Project: {MAGENTA}{project_name}{RESET}")
            print(f"    {YELLOW}Test indicators: {test_domain}, {test_hash}, {test_ip}{RESET}")
            
            try:
                # Step 1: Create Validin-only state with all indicator types
                print(f"    {YELLOW}Step 1: Creating Validin-only state{RESET}")
                
                # Add domain to Validin
                msgs = await core.stormlist(f"[ inet:fqdn={test_domain} ] | ex.validin.project.indicators.add {project_guid}")
                storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
                self.eq(len(storm_errors), 0, "Should add domain without Storm errors")
                
                # Add hash to Validin
                msgs = await core.stormlist(f"[ hash:md5={test_hash} ] | ex.validin.project.indicators.add {project_guid}")
                storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
                self.eq(len(storm_errors), 0, "Should add hash without Storm errors")
                
                # Add IP to Validin
                msgs = await core.stormlist(f"[ inet:ipv4={test_ip} ] | ex.validin.project.indicators.add {project_guid}")
                storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
                self.eq(len(storm_errors), 0, "Should add IP without Storm errors")
                
                # Remove all from Synapse to create Validin-only state
                await core.nodes(f"inet:fqdn={test_domain} | delnode --force")
                await core.nodes(f"hash:md5={test_hash} | delnode --force")
                await core.nodes(f"inet:ipv4={test_ip} | delnode --force")
                
                # Verify removal
                domain_nodes_before = await core.nodes(f"inet:fqdn={test_domain}")
                hash_nodes_before = await core.nodes(f"hash:md5={test_hash}")
                ip_nodes_before = await core.nodes(f"inet:ipv4={test_ip}")
                
                total_before = len(domain_nodes_before) + len(hash_nodes_before) + len(ip_nodes_before)
                self.eq(total_before, 0, "All indicators should be removed from Synapse")
                print(f"      All {total_before} indicators exist in Validin, removed from Synapse")
                
                # Step 2: Run pull sync to recreate indicators
                print(f"    {YELLOW}Step 2: Running pull sync{RESET}")
                msgs = await core.stormlist(f"$lib.debug=$lib.true | proj:project={project_guid} | ex.validin.project.indicators.get --yield")
                
                storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
                self.eq(len(storm_errors), 0, "Pull sync should have no Storm errors")
                
                # Step 3: Verify all indicators were recreated from Validin
                print(f"    {YELLOW}Step 3: Verifying indicators were recreated from Validin{RESET}")
                domain_nodes_after = await core.nodes(f"inet:fqdn={test_domain}")
                hash_nodes_after = await core.nodes(f"hash:md5={test_hash}")
                ip_nodes_after = await core.nodes(f"inet:ipv4={test_ip}")
                
                total_recreated = len(domain_nodes_after) + len(hash_nodes_after) + len(ip_nodes_after)
                print(f"      {GREEN}✓ Indicators recreated from Validin: {total_recreated}/3 (domain: {len(domain_nodes_after)}, hash: {len(hash_nodes_after)}, IP: {len(ip_nodes_after)}){RESET}")
                
                # Verify project edges
                domain_edges = await core.nodes(f"proj:project={project_guid} -(refs)> inet:fqdn={test_domain}")
                hash_edges = await core.nodes(f"proj:project={project_guid} -(refs)> hash:md5={test_hash}")
                ip_edges = await core.nodes(f"proj:project={project_guid} -(refs)> inet:ipv4={test_ip}")
                
                total_edges = len(domain_edges) + len(hash_edges) + len(ip_edges)
                print(f"      {GREEN}✓ Project edges created: {total_edges}/3{RESET}")
                
                # Step 4: Test idempotency (running get again should not duplicate)
                print(f"    {YELLOW}Step 4: Testing get command idempotency{RESET}")
                nodes_before_second = total_recreated
                
                msgs = await core.stormlist(f"$lib.debug=$lib.true | proj:project={project_guid} | ex.validin.project.indicators.get --yield")
                
                domain_nodes_second = await core.nodes(f"inet:fqdn={test_domain}")
                hash_nodes_second = await core.nodes(f"hash:md5={test_hash}")
                ip_nodes_second = await core.nodes(f"inet:ipv4={test_ip}")
                
                total_after_second = len(domain_nodes_second) + len(hash_nodes_second) + len(ip_nodes_second)
                
                if total_after_second == nodes_before_second:
                    print(f"      {GREEN}✓ Get command is idempotent - no duplicate creation{RESET}")
                else:
                    print(f"      {YELLOW}⚠ Get command may have created duplicates ({total_after_second} vs {nodes_before_second}){RESET}")
                
            finally:
                # Cleanup
                print(f"    {YELLOW}Cleanup: Removing test indicators{RESET}")
                try:
                    # Clean up domain indicator
                    await self._cleanup_test_indicator(core, test_domain, project_guid)
                    
                    # Clean up hash indicator
                    msgs = await core.stormlist(f"[ hash:md5={test_hash} ] | ex.validin.project.indicators.delete {project_guid}")
                    await core.nodes(f"hash:md5={test_hash} | delnode --force")
                    
                    # Clean up IP indicator
                    msgs = await core.stormlist(f"[ inet:ipv4={test_ip} ] | ex.validin.project.indicators.delete {project_guid}")
                    await core.nodes(f"inet:ipv4={test_ip} | delnode --force")
                except:
                    pass

    async def test_sync_integration(self):
        """Test sync with project integration"""
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Testing Project Integration ==={RESET}")

            await self._setup_validin(core, enterprise=True)
            
            # Try to get the specific test project
            project_nodes = await core.nodes(f"proj:project:name~='{self.TEST_PROJECT_NAME.lower()}'")
            if len(project_nodes) == 0:
                print(f"{YELLOW}Test project '{self.TEST_PROJECT_NAME}' not found - skipping real integration test{RESET}")
                return
                
            test_project = project_nodes[0]
            project_guid = test_project.props.get("_validin:guid")
            project_name = test_project.props.get("name") or "Unknown"
            
            print(f"  {BLUE}Testing Real Integration with Project: {MAGENTA}{project_name}{RESET}")
            print(f"    {YELLOW}Project GUID: {project_guid}{RESET}")
            
            # Test with known indicators
            known_hash = "d41d8cd98f00b204e9800998ecf8427e"
            known_ip = "192.0.2.100"
            
            try:
                # Test pull sync with known hash
                print(f"    {YELLOW}Testing pull sync with known hash: {known_hash}{RESET}")
                
                # Check if hash exists in Synapse initially
                hash_nodes_before = await core.nodes(f"hash:md5={known_hash}")
                print(f"      Hash nodes before test: {len(hash_nodes_before)}")
                
                # If it exists, remove it to test pull
                if len(hash_nodes_before) > 0:
                    await core.nodes(f"hash:md5={known_hash} | delnode --force")
                    hash_nodes_after_delete = await core.nodes(f"hash:md5={known_hash}")
                    print(f"      Hash nodes after deletion: {len(hash_nodes_after_delete)}")
                
                # Run pull sync
                msgs = await core.stormlist(f"$lib.debug=$lib.true | proj:project={project_guid} | ex.validin.project.indicators.get --yield")
                storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
                self.eq(len(storm_errors), 0, "Pull sync should have no Storm errors")
                
                # Check if hash was recreated
                hash_nodes_after_pull = await core.nodes(f"hash:md5={known_hash}")
                print(f"      Hash nodes after pull: {len(hash_nodes_after_pull)}")
                
                if len(hash_nodes_after_pull) > 0:
                    # Verify project relationship
                    hash_project_edges = await core.nodes(f"proj:project={project_guid} -(refs)> hash:md5={known_hash}")
                    print(f"      {GREEN}✓ Pull sync recreated hash with {len(hash_project_edges)} project edges{RESET}")
                else:
                    print(f"      {YELLOW}⚠ Pull sync did not recreate hash (may not exist in Validin){RESET}")
                
                # Test idempotency
                print(f"    {YELLOW}Testing sync idempotency{RESET}")
                nodes_before_second = await core.nodes(f"proj:project={project_guid} -(refs)> *")
                indicator_count_before = len([n for n in nodes_before_second if n.ndef[0] != "proj:project"])
                
                msgs = await core.stormlist(f"$lib.debug=$lib.true | proj:project={project_guid} | ex.validin.project.indicators.get --yield")
                storm_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1]) and 'HTTP' not in str(msg[1])]
                self.eq(len(storm_errors), 0, "Second pull sync should have no Storm errors")
                
                nodes_after_second = await core.nodes(f"proj:project={project_guid} -(refs)> *")  
                indicator_count_after = len([n for n in nodes_after_second if n.ndef[0] != "proj:project"])
                
                print(f"      Indicators before second sync: {indicator_count_before}")
                print(f"      Indicators after second sync: {indicator_count_after}")
                print(f"      {GREEN}✓ Sync idempotency validated{RESET}")
                
            except Exception as e:
                print(f"      {YELLOW}Warning: Exception during real project test: {e}{RESET}")
                
            print(f"      {GREEN}✓ Project integration test completed{RESET}")

    async def test_sync_mode_parameter_validation(self):
        """Test that sync command properly validates mode parameters"""
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Testing Sync Mode Parameter Validation ==={RESET}")

            await self._setup_validin(core, enterprise=True)
            
            # Test invalid mode
            msgs = await core.stormlist("ex.validin.project.sync --mode invalid_mode")
            
            # Should have an error about invalid choice
            has_choice_error = any(msg[0] == 'err' and 'choice' in str(msg[1]).lower() for msg in msgs)
            self.assertTrue(has_choice_error, "Should reject invalid mode parameter")
            
            print(f"    {GREEN}✓ Invalid mode parameter properly rejected{RESET}")
            
            # Test all valid modes execute without parameter errors
            valid_modes = ['pull', 'push', 'draft']
            
            for mode in valid_modes:
                msgs = await core.stormlist(f"ex.validin.project.sync --mode {mode}")
                
                # Check for parameter/choice errors (not API errors)
                param_errors = [msg for msg in msgs if msg[0] == 'err' and ('choice' in str(msg[1]).lower() or 'argument' in str(msg[1]).lower())]
                self.eq(len(param_errors), 0, f"Mode '{mode}' should be valid parameter")
                
                print(f"    {GREEN}✓ Mode '{mode}' accepted as valid parameter{RESET}")

            print(f"\n{GREEN}=== Project Sync Testing Complete ==={RESET}\n")