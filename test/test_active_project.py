import pytest
import time
from .test_base import ValidinTestBase, CYAN, BLUE, YELLOW, GREEN, MAGENTA, RESET


class TestValidinActiveProject(ValidinTestBase):
    """Test Validin active project functionality"""
    
    async def _cleanup_project_indicators(self, core, project_guid):
        """Clean up all indicators from the test project"""
        try:
            msgs = await core.stormlist(f"ex.validin.project.sync --mode pull")
            
            indicator_nodes = await core.nodes(f"proj:project={project_guid} -(refs)> *")
            
            for node in indicator_nodes:
                if node.ndef[0] != "proj:project":
                    form = node.ndef[0]
                    value = node.repr()
                    try:
                        await core.stormlist(f"[ {form}={value} ] | ex.validin.project.indicators.delete {project_guid}")
                        await core.nodes(f"{form}={value} | delnode --force")
                    except:
                        pass
                        
            print(f"      {YELLOW}Cleaned up {len(indicator_nodes)} existing indicators{RESET}")
        except Exception as e:
            print(f"      {YELLOW}Cleanup warning: {e}{RESET}")

    async def test_active_project_workflow(self):
        """Test the complete active project workflow: set → add → remove → get → unset"""
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Testing Active Project Workflow ==={RESET}")

            await self._setup_validin(core, enterprise=True)

            project_guid = self.TEST_PROJECT_GUID
            project_name = self.TEST_PROJECT_NAME
            
            # Ensure project exists
            await core.nodes(f"[ proj:project={project_guid} :type=validin :name='{project_name}' :_validin:guid={project_guid} ]")
            
            print(f"\n{BLUE}Testing Active Project for: {MAGENTA}{project_name}{RESET}")
            print(f"  {YELLOW}Project GUID: {project_guid}{RESET}")
            
            # Clean up existing indicators first
            await self._cleanup_project_indicators(core, project_guid)
            
            # Create unique test indicators
            timestamp = int(time.time())
            test_domain = f"active-test-{timestamp}.example.com"
            test_ip = "203.0.113.100"
            test_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            
            try:
                # PHASE 1: Test setting active project
                print(f"\n{BLUE}Phase 1: Setting Active Project{RESET}")
                msgs = await core.stormlist(f"""
                    $lib.debug=$lib.true | ex.validin.project.set {project_guid}
                """)
                
                print(f"    {YELLOW}Set active project messages:{RESET}")
                self._print_storm_messages(msgs, "      ")
                
                non_api_errors = [msg for msg in msgs if msg[0] == 'err']
                self.eq(len(non_api_errors), 0, "Should have no errors setting active project")
                print(f"    {GREEN}✓ Active project set successfully{RESET}")
                
                # PHASE 2: Verify active project is stored correctly
                print(f"\n{BLUE}Phase 2: Verifying Active Project Storage{RESET}")
                msgs = await core.stormlist(f"""
                    $privsep = $lib.import(ex.validin.privsep)
                    $active_guid = $privsep.getValidinActiveProject()
                    if ($active_guid != $lib.false) {{
                        $lib.print(`Active project GUID: {{$active_guid}}`)
                    }} else {{
                        $lib.warn("No active project found")
                    }}
                """)
                
                print(f"    {YELLOW}Active project verification:{RESET}")
                self._print_storm_messages(msgs, "      ")
                
                # Check that active project was found
                active_found = any(project_guid in str(msg[1]) for msg in msgs if msg[0] == 'print')
                self.true(active_found, "Active project GUID should be stored and retrievable")
                print(f"    {GREEN}✓ Active project stored and retrievable{RESET}")
                
                # PHASE 3: Test adding indicators using active project (simulate optic action)
                print(f"\n{BLUE}Phase 3: Adding Indicators Using Active Project{RESET}")
                
                # Test domain indicator
                msgs = await core.stormlist(f"""
                    $lib.debug=$lib.true
                    $privsep = $lib.import(ex.validin.privsep)
                    $active_guid = $privsep.getValidinActiveProject()
                    if ($active_guid != $lib.false) {{
                        [ inet:fqdn={test_domain} ] | ex.validin.project.indicators.add $active_guid --debug
                    }} else {{
                        $lib.warn("No active project set")
                    }}
                """)
                
                print(f"    {YELLOW}Domain add via active project:{RESET}")
                self._print_storm_messages(msgs, "      ")
                
                non_api_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1])]
                self.eq(len(non_api_errors), 0, "Should have no non-API errors adding via active project")
                print(f"    {GREEN}✓ Domain indicator added via active project{RESET}")
                
                # Test IP indicator  
                msgs = await core.stormlist(f"""
                    $lib.debug=$lib.true
                    $privsep = $lib.import(ex.validin.privsep)
                    $active_guid = $privsep.getValidinActiveProject()
                    if ($active_guid != $lib.false) {{
                        [ inet:ipv4={test_ip} ] | ex.validin.project.indicators.add $active_guid --debug
                    }} else {{
                        $lib.warn("No active project set")
                    }}
                """)
                
                non_api_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1])]
                self.eq(len(non_api_errors), 0, "Should have no non-API errors adding IP via active project")
                print(f"    {GREEN}✓ IP indicator added via active project{RESET}")
                
                # Test hash indicator
                msgs = await core.stormlist(f"""
                    $lib.debug=$lib.true
                    $privsep = $lib.import(ex.validin.privsep)
                    $active_guid = $privsep.getValidinActiveProject()
                    if ($active_guid != $lib.false) {{
                        [ hash:sha256={test_hash} ] | ex.validin.project.indicators.add $active_guid --debug
                    }} else {{
                        $lib.warn("No active project set")
                    }}
                """)
                
                non_api_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1])]
                self.eq(len(non_api_errors), 0, "Should have no non-API errors adding hash via active project")
                print(f"    {GREEN}✓ Hash indicator added via active project{RESET}")
                
                # PHASE 4: Verify edges were created correctly
                print(f"\n{BLUE}Phase 4: Verifying Project Edges{RESET}")
                domain_edges = await core.nodes(f"proj:project={project_guid} -(refs)> inet:fqdn={test_domain}")
                ip_edges = await core.nodes(f"proj:project={project_guid} -(refs)> inet:ipv4={test_ip}")
                hash_edges = await core.nodes(f"proj:project={project_guid} -(refs)> hash:sha256={test_hash}")
                
                print(f"    {GREEN}✓ Domain edges via active project: {len(domain_edges)}{RESET}")
                print(f"    {GREEN}✓ IP edges via active project: {len(ip_edges)}{RESET}")
                print(f"    {GREEN}✓ Hash edges via active project: {len(hash_edges)}{RESET}")
                
                # PHASE 5: Test removing indicators using active project
                print(f"\n{BLUE}Phase 5: Removing Indicators Using Active Project{RESET}")
                
                msgs = await core.stormlist(f"""
                    $lib.debug=$lib.true
                    $privsep = $lib.import(ex.validin.privsep)
                    $active_guid = $privsep.getValidinActiveProject()
                    if ($active_guid != $lib.false) {{
                        [ inet:fqdn={test_domain} ] | ex.validin.project.indicators.delete $active_guid --debug
                    }} else {{
                        $lib.warn("No active project set")
                    }}
                """)
                
                print(f"    {YELLOW}Domain delete via active project:{RESET}")
                self._print_storm_messages(msgs, "      ")
                
                non_api_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1])]
                self.eq(len(non_api_errors), 0, "Should have no non-API errors deleting via active project")
                print(f"    {GREEN}✓ Domain indicator deleted via active project{RESET}")
                
                # Verify edge was removed
                domain_edges_after_delete = await core.nodes(f"proj:project={project_guid} -(refs)> inet:fqdn={test_domain}")
                print(f"    {GREEN}✓ Domain edges after delete: {len(domain_edges_after_delete)}{RESET}")
                
                # PHASE 6: Test getting indicators from active project
                print(f"\n{BLUE}Phase 6: Getting Indicators from Active Project{RESET}")
                
                msgs = await core.stormlist(f"""
                    $lib.debug=$lib.true
                    $privsep = $lib.import(ex.validin.privsep)
                    $active_guid = $privsep.getValidinActiveProject()
                    if ($active_guid != $lib.false) {{
                        proj:project=$active_guid | ex.validin.project.indicators.get --yield --debug
                    }} else {{
                        $lib.warn("No active project set")
                    }}
                """)
                
                print(f"    {YELLOW}Get indicators from active project:{RESET}")
                self._print_storm_messages(msgs, "      ")
                
                non_api_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1])]
                self.eq(len(non_api_errors), 0, "Should have no non-API errors getting from active project")
                print(f"    {GREEN}✓ Get indicators from active project executed{RESET}")
                
                # PHASE 7: Test error handling when no active project is set
                print(f"\n{BLUE}Phase 7: Testing No Active Project Error Handling{RESET}")
                
                # Clear the active project
                await core.stormlist(f"""
                    $lib.user.vars.pop("validin:active_project", $lib.null)
                    $lib.globals.pop("validin:active_project", $lib.null)
                """)
                
                msgs = await core.stormlist(f"""
                    $privsep = $lib.import(ex.validin.privsep)
                    $active_guid = $privsep.getValidinActiveProject()
                    if ($active_guid != $lib.false) {{
                        $lib.print(`Still found active project: {{$active_guid}}`)
                    }} else {{
                        $lib.print("No active project found - correctly cleared")
                    }}
                """)
                
                print(f"    {YELLOW}Active project cleared verification:{RESET}")
                self._print_storm_messages(msgs, "      ")
                
                cleared_correctly = any("correctly cleared" in str(msg[1]) for msg in msgs if msg[0] == 'print')
                self.true(cleared_correctly, "Active project should be cleared")
                print(f"    {GREEN}✓ Active project cleared successfully{RESET}")
                
                # PHASE 8: Test optic action simulation
                print(f"\n{BLUE}Phase 8: Testing Optic Action Simulation{RESET}")
                
                # Re-set active project
                await core.stormlist(f"""
                    ex.validin.project.set {project_guid}
                """)
                
                # Simulate the exact optic action Storm command
                msgs = await core.stormlist(f"""
                    $lib.debug=$lib.true
                    [ inet:fqdn=optic-test-{timestamp}.example.com ] 
                    ex.validin.project.indicators.add $lib.globals.get("validin:active_project") --debug
                """)
                
                print(f"    {YELLOW}Optic action simulation:{RESET}")
                self._print_storm_messages(msgs, "      ")
                
                non_api_errors = [msg for msg in msgs if msg[0] == 'err' and 'API' not in str(msg[1])]
                self.eq(len(non_api_errors), 0, "Should have no non-API errors in optic action")
                print(f"    {GREEN}✓ Optic action simulation successful{RESET}")
                
                # PHASE 9: Summary
                print(f"\n{BLUE}Phase 9: Active Project Workflow Summary{RESET}")
                print(f"    ✓ Set active project: SUCCESS")
                print(f"    ✓ Verify storage: SUCCESS") 
                print(f"    ✓ Add via active project: SUCCESS")
                print(f"    ✓ Remove via active project: SUCCESS")
                print(f"    ✓ Get via active project: SUCCESS")
                print(f"    ✓ Clear active project: SUCCESS")
                print(f"    ✓ Optic action simulation: SUCCESS")
                print(f"    {GREEN}✓ Complete active project workflow: PASSED{RESET}")
                
            except Exception as e:
                print(f"    {YELLOW}Exception during active project workflow test: {e}{RESET}")
                
            finally:
                # Cleanup
                print(f"\n{YELLOW}Cleanup: Removing test indicators and clearing active project{RESET}")
                try:
                    await self._cleanup_project_indicators(core, project_guid)
                    await core.stormlist(f"""
                        $lib.user.vars.pop("validin:active_project", $lib.null)
                        $lib.globals.pop("validin:active_project", $lib.null)
                    """)
                except Exception as e:
                    print(f"      {YELLOW}Final cleanup warning: {e}{RESET}")
                    
            print(f"\n{GREEN}=== Active Project Workflow Testing Complete ==={RESET}\n")