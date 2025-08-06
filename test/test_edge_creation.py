import pytest
from .test_base import ValidinTestBase, CYAN, BLUE, YELLOW, GREEN, MAGENTA, RESET


class TestEdgeCreation(ValidinTestBase):
    """Test edge creation patterns"""
    
    async def test_manual_edge_creation(self):
        """Test manual edge creation patterns"""
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Testing Manual Edge Creation ==={RESET}")
            
            await self._setup_validin(core, enterprise=True)
            
            project_guid = self.TEST_PROJECT_GUID
            test_domain = "edge-test.example.com"
            
            # Step 1: Ensure project exists
            print(f"\n{BLUE}Step 1: Creating project node{RESET}")
            project_nodes = await core.nodes(f"[ proj:project={project_guid} :type=validin ]")
            print(f"  Project nodes created: {len(project_nodes)}")
            
            # Step 2: Create indicator with atomic edge using Storm command
            print(f"\n{BLUE}Step 2: Creating indicator with atomic edge{RESET}")
            msgs = await core.stormlist(f"""
                [ proj:project={project_guid} ]
                [ inet:fqdn={test_domain} <(refs)+ {{ proj:project={project_guid} }} ]
            """)
            
            # Check for errors
            errors = [msg for msg in msgs if msg[0] == 'err']
            if errors:
                print(f"  {YELLOW}Errors during creation: {errors}{RESET}")
            
            # Step 3: Check if indicator was created
            print(f"\n{BLUE}Step 3: Verifying indicator creation{RESET}")
            domain_nodes = await core.nodes(f"inet:fqdn={test_domain}")
            print(f"  Domain nodes created: {len(domain_nodes)}")
            
            # Step 4: Check edges in BOTH directions
            print(f"\n{BLUE}Step 4: Testing edge directions{RESET}")
            
            # Forward direction (correct)
            forward_edges = await core.nodes(f"proj:project={project_guid} -(refs)> inet:fqdn={test_domain}")
            print(f"  Forward edges (project -> domain): {len(forward_edges)}")
            
            # Backward direction (should be 0)
            backward_edges = await core.nodes(f"inet:fqdn={test_domain} -(refs)> proj:project={project_guid}")
            print(f"  Backward edges (domain -> project): {len(backward_edges)}")
            
            # Step 5: Try creating edge separately (to see if it works)
            print(f"\n{BLUE}Step 5: Testing separate edge creation{RESET}")
            msgs = await core.stormlist(f"""
                inet:fqdn={test_domain} [ <(refs)+ {{ proj:project={project_guid} }} ]
            """)
            
            errors = [msg for msg in msgs if msg[0] == 'err']
            if errors:
                print(f"  {YELLOW}Errors during separate edge: {errors}{RESET}")
            
            # Check edges again
            forward_edges_after = await core.nodes(f"proj:project={project_guid} -(refs)> inet:fqdn={test_domain}")
            print(f"  Forward edges after separate creation: {len(forward_edges_after)}")
            
            # Step 6: Test with the actual privsep function
            print(f"\n{BLUE}Step 6: Testing privsep.createProjectIndicator{RESET}")
            test_domain2 = "edge-test-2.example.com"
            msgs = await core.stormlist(f"""
                $privsep = $lib.import(ex.validin.privsep, debug=$lib.true)
                $result = $privsep.createProjectIndicator("{project_guid}", "inet:fqdn", "{test_domain2}")
                
                // Check if indicator was created by trying to find it
                $found_indicator = $lib.false
                inet:fqdn={test_domain2} {{ $found_indicator = $lib.true }}
                
                // Check if edge was created
                $found_edge = $lib.false
                proj:project={project_guid} -(refs)> inet:fqdn={test_domain2} {{ $found_edge = $lib.true }}
                
                $lib.print(`Storm context: found_indicator=${{$found_indicator}}, found_edge=${{$found_edge}}, function_result=${{$result}}`)
                
                // Yield the created nodes to test context  
                inet:fqdn={test_domain2}
            """)
            
            # Print all messages for debugging
            for msg in msgs:
                if msg[0] in ['print', 'warn', 'err']:
                    print(f"  {msg[0]}: {msg[1].get('mesg', msg[1]) if isinstance(msg[1], dict) else msg[1]}")
            
            # Check if indicator 2 was created with edge (should work now)
            domain2_nodes = await core.nodes(f"inet:fqdn={test_domain2}")
            domain2_edges = await core.nodes(f"proj:project={project_guid} -(refs)> inet:fqdn={test_domain2}")
            print(f"  Domain 2 nodes: {len(domain2_nodes)}, edges: {len(domain2_edges)}")
            
            # Cleanup
            await core.nodes(f"inet:fqdn={test_domain} | delnode --force")
            await core.nodes(f"inet:fqdn={test_domain2} | delnode --force")
            
            # Summary
            print(f"\n{BLUE}Summary:{RESET}")
            if forward_edges_after or domain2_edges:
                print(f"  {GREEN}✓ Edge creation is working!{RESET}")
            else:
                print(f"  {YELLOW}⚠ Edge creation needs investigation{RESET}")

    async def test_edge_direction_verification(self):
        """Verify which edge direction is correct"""
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Testing Edge Direction Verification ==={RESET}")
            
            await self._setup_validin(core, enterprise=True)
            
            project_guid = self.TEST_PROJECT_GUID
            test_hash = "d41d8cd98f00b204e9800998ecf8427e"
            
            # Create project
            await core.nodes(f"[ proj:project={project_guid} :type=validin ]")
            
            # Test different edge creation syntaxes
            print(f"\n{BLUE}Testing different edge syntaxes:{RESET}")
            
            # Syntax 1: Edge in same brackets as node creation
            print(f"\n  Testing: [ hash:md5={test_hash} <(refs)+ {{ proj:project={project_guid} }} ]")
            msgs = await core.stormlist(f"""
                [ hash:md5={test_hash} <(refs)+ {{ proj:project={project_guid} }} ]
            """)
            
            hash_nodes = await core.nodes(f"hash:md5={test_hash}")
            forward_edges = await core.nodes(f"proj:project={project_guid} -(refs)> hash:md5={test_hash}")
            backward_edges = await core.nodes(f"hash:md5={test_hash} -(refs)> proj:project={project_guid}")
            
            print(f"    Nodes: {len(hash_nodes)}, Forward: {len(forward_edges)}, Backward: {len(backward_edges)}")
            
            # Clean up for next test
            await core.nodes(f"hash:md5={test_hash} | delnode --force")
            
            # Syntax 2: Ensure both nodes exist first
            print(f"\n  Testing: Ensure nodes exist, then create edge")
            msgs = await core.stormlist(f"""
                [ proj:project={project_guid} ]
                [ hash:md5={test_hash} ]
                hash:md5={test_hash} [ <(refs)+ {{ proj:project={project_guid} }} ]
            """)
            
            hash_nodes = await core.nodes(f"hash:md5={test_hash}")
            forward_edges = await core.nodes(f"proj:project={project_guid} -(refs)> hash:md5={test_hash}")
            backward_edges = await core.nodes(f"hash:md5={test_hash} -(refs)> proj:project={project_guid}")
            
            print(f"    Nodes: {len(hash_nodes)}, Forward: {len(forward_edges)}, Backward: {len(backward_edges)}")
            
            # Determine correct direction
            if forward_edges:
                print(f"  {GREEN}✓ Edge direction confirmed: project -(refs)> indicator{RESET}")
            elif backward_edges:
                print(f"  {YELLOW}⚠ Edge direction is: indicator -(refs)> project{RESET}")
            else:
                print(f"  {YELLOW}⚠ No edges created{RESET}")
            
            # Cleanup
            await core.nodes(f"hash:md5={test_hash} | delnode --force")