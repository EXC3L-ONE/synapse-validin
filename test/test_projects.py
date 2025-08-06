import pytest
from .test_base import ValidinTestBase, CYAN, BLUE, YELLOW, GREEN, MAGENTA, RESET


class TestValidinProjects(ValidinTestBase):
    """Test basic Validin project functionality"""

    async def test_projects(self):
        """Test basic project functionality focusing on Storm syntax validation"""
        async with self.getTestCore() as core:
            print(f"\n{CYAN}=== Starting Project Testing ==={RESET}")

            # Setup Validin (use enterprise since projects are enterprise feature)
            await self._setup_validin(core, enterprise=True)

            # PHASE 1: Test Basic Project List
            print(f"\n{BLUE}Phase 1: Testing Basic Project List{RESET}")
            
            msgs = await core.stormlist("$lib.debug=$lib.true | ex.validin.project.list --yield")
            self.stormHasNoWarnErr(msgs)
            
            # Verify we can retrieve projects without Storm syntax errors
            project_nodes = await core.nodes("proj:project:type=validin")
            print(f"{YELLOW}Found {len(project_nodes)} proj:project nodes{RESET}")
            
            # Show project details
            for project in project_nodes:
                project_name = project.get("name")
                validin_guid = project.get("_validin:guid")
                if project_name:
                    print(f"  {MAGENTA}Project:{RESET} {project_name}")
                    if validin_guid:
                        print(f"    {GREEN}✓ Has Validin GUID: {validin_guid}{RESET}")
            
            # PHASE 2: Test Project Indicator Retrieval
            print(f"\n{BLUE}Phase 2: Testing Project Indicator Retrieval{RESET}")
            
            if len(project_nodes) > 0:
                test_project = project_nodes[0]
                project_guid = test_project.get("_validin:guid") or str(test_project.ndef[1])
                project_name = test_project.get("name") or "Unknown"
                
                print(f"  {YELLOW}Testing indicators for '{project_name}'{RESET}")
                
                # Test basic indicator retrieval (existing functionality)
                msgs = await core.stormlist(f"""
                    $lib.debug=$lib.true | proj:project={project_guid} | ex.validin.project.indicators.get --yield
                """)
                self.stormHasNoWarnErr(msgs)
                print(f"    {GREEN}✓ Project indicator retrieval syntax valid{RESET}")
                
                # Check if any indicators were created and linked
                indicator_nodes = await core.nodes(f"proj:project={project_guid} -(refs)> *")
                indicator_count = len([n for n in indicator_nodes if n.ndef[0] != "proj:project"])
                print(f"    {GREEN}✓ Found {indicator_count} linked indicators{RESET}")
            
            print(f"\n{GREEN}=== Project Testing Complete - No Storm Syntax Errors ==={RESET}\n")