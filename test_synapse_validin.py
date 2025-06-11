import os
from dotenv import load_dotenv

import synapse.tests.utils as s_test

dirname = os.path.abspath(os.path.dirname(__file__))
# Load env
load_dotenv(os.path.join(dirname, '.env'))
if not os.getenv('VALIDIN_API_KEY'):
    raise ValueError('VALIDIN_API_KEY environment variable is not set. Please check your .env file.')

class AcmeValidinTest(s_test.StormPkgTest):

    pkgprotos = (os.path.join(dirname, 'synapse-validin.yaml'),)

    async def test_setting_api_key(self):
        async with self.getTestCore() as core:
            # Test setting API key for current user
            msgs = await core.stormlist(f'ex.validin.setup.apikey --self --debug {os.getenv("VALIDIN_API_KEY")}')
            self.stormIsInPrint('Setting Validin API key for the current user', msgs)
            self.stormHasNoWarnErr(msgs)

    async def test_pdns(self):
        async with self.getTestCore() as core:
            # Set up API key
            msgs = await core.stormlist(f'ex.validin.setup.apikey --self --debug {os.getenv("VALIDIN_API_KEY")}')
            self.stormHasNoWarnErr(msgs)

            # Create IPv4 node and test PDNS enrichment
            msgs = await core.stormlist('''
                [ inet:ipv4=1.1.1.1 ]
                | ex.validin.pdns --debug
            ''')
            
            # Verify results
            self.stormHasNoWarnErr(msgs)
            
            # Verify creation of DNS records
            nodes = await core.nodes('inet:dns:a')
            self.gt(len(nodes), 0)  # >= 1 node

""" for manual testing/debugging, uncomment the following lines
def main():

    test = AcmeValidinTest()
    test.test_setting_api_key()
    test.test_pdns()

main() 
"""
