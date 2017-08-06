import json
import requests
import logging

logging.captureWarnings(True)

INFO_REQUEST = {
    "i2p.router.uptime": "",
    "i2p.router.net.status": "",
    "i2p.router.netdb.knownpeers": "",
    "i2p.router.netdb.activepeers": "",
    "i2p.router.net.bw.inbound.1s": "",
    "i2p.router.net.bw.outbound.1s": "",
    "i2p.router.net.tunnels.participating": "",
    "i2p.router.net.tunnels.successrate": "",
    "i2p.router.net.total.received.bytes": "",
    "i2p.router.net.total.sent.bytes": "",
}

STATUS = [
    "OK",
    "TESTING",
    "FIREWALLED",
    "HIDDEN",
    "WARN_FIREWALLED_AND_FAST",
    "WARN_FIREWALLED_AND_FLOODFILL",
    "WARN_FIREWALLED_WITH_INBOUND_TCP",
    "WARN_FIREWALLED_WITH_UDP_DISABLED",
    "ERROR_I2CP",
    "ERROR_CLOCK_SKEW",
    "ERROR_PRIVATE_TCP_ADDRESS",
    "ERROR_SYMMETRIC_NAT",
    "ERROR_UDP_PORT_IN_USE",
    "ERROR_NO_ACTIVE_PEERS_CHECK_CONNECTION_AND_FIREWALL",
    "ERROR_UDP_DISABLED_AND_TCP_UNSET",
]

def get_token(url, password='itoopie'):
    """Get I2PControl token"""
    return requests.post(
            url,
            json.dumps({'id': 1, 'method': 'Authenticate', 
                'params': {'API': 1, 'Password': 'itoopie'}, 'jsonrpc': '2.0'}),
            verify=False).json()["result"]["Token"]

def request(url, token, method, params):
    """Execute authenticated I2PControl request"""
    return requests.post(
        url, 
        json.dumps({'id': 1, 'method': method, 'params': params, 
            'jsonrpc': '2.0', 'Token': token}),
        verify=False
    ).json() 

