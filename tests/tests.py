from unittest import TestCase
from unittest.mock import MagicMock

from testnet.testnet import I2pd, Testnet

class I2pdTests(TestCase):
    """Cli app tests"""

    def test_create(self):
        netname = 'test'
        cont = MagicMock()
        cont.id = "8fddbcbb101c8fddbcbb101c8fddbcbb101c"
        cont.attrs = {'NetworkSettings':
                {'Networks': {netname: {'IPAddress': '172.18.0.3'}}}}

        i2pd = I2pd(cont, netname)
        i2pd.control = MagicMock()
        i2pd.control.request.return_value = {'result': {
            'i2p.router.net.bw.inbound.1s': 0.0,
            'i2p.router.net.bw.outbound.1s': 0.0,
            'i2p.router.net.status': 0,
            'i2p.router.net.total.received.bytes': 165940.0,
            'i2p.router.net.total.sent.bytes': 161520.0,
            'i2p.router.net.tunnels.participating': 25,
            'i2p.router.net.tunnels.successrate': 100,
            'i2p.router.netdb.activepeers': 5,
            'i2p.router.netdb.knownpeers': 5,
            'i2p.router.uptime': 39000
        }}

        self.assertEqual(i2pd.id, "8fddbcbb101c")
        self.assertEqual(i2pd.ip, "172.18.0.3")

        info = i2pd.info_str()
        self.assertEqual(info, 
            '8fddbcbb101c\t172.18.0.3\tOK\t100%\t5/5\t165940.0/161520.0\t25')
        

class TestnetTests(TestCase):

    def test_start(self):
        cli = MagicMock()
        testnet = Testnet(cli)

        testnet.create_network()
        testnet.cli.networks.create.assert_called_once_with(
                'i2pdtestnet', driver="bridge", internal=True)

        testnet.init_floodfills()
        self.assertEqual(len(testnet.NODES), 1)
        testnet.run_pyseeder()


