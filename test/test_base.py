import os
from dotenv import load_dotenv
import synapse.tests.utils as s_test

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


class ValidinTestBase(s_test.StormPkgTest):
    """Base test class for Validin Power-Up tests"""
    
    pkgprotos = (os.path.join(parent_dir, "synapse-validin.yaml"),)
    
    @property
    def TEST_PROJECT_GUID(self):
        """Get test project GUID from environment variables"""
        return os.getenv('TEST_PROJECT_GUID', 'a878de86-d38f-4a89-adf1-e7299129cd33')
    
    @property 
    def TEST_PROJECT_NAME(self):
        """Get test project name from environment variables"""
        return os.getenv('TEST_PROJECT_NAME', 'Watchlist used for Unit Testing Validin Power-up')
    
    def _extract_message(self, msg):
        """Safely extract message content from Synapse message tuple"""
        if isinstance(msg[1], dict):
            return msg[1].get('mesg', msg[1])
        else:
            return msg[1]
    
    def _print_storm_messages(self, msgs, prefix=""):
        """Print Storm messages with consistent formatting"""
        for msg in msgs:
            if msg[0] in ['print', 'warn', 'err']:
                mesg = self._extract_message(msg)
                print(f"{prefix}{msg[0]}: {mesg}")

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