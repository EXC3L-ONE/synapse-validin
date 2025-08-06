import os
import pytest
from .test_base import ValidinTestBase, CYAN, BLUE, YELLOW, GREEN, MAGENTA, RESET


class TestValidinSetup(ValidinTestBase):
    """Test Validin API key and hostname configuration"""

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