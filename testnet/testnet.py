import os
import random
import string

import requests

from testnet import i2pcontrol


def rand_string(length=8):
    """Generate lame random hexdigest string"""
    return "".join([random.choice(string.hexdigits) for _ in range(length)])


class I2pd(object):
    """i2pd node object"""
    def __init__(self, container, netname):
        container.reload()
        self.id = container.id[:12]
        self.container = container
        self.netname = netname
        self.ip = container.attrs['NetworkSettings']['Networks'][
                self.netname]['IPAddress']
        self.URLS = {
            'Control': "https://{}:7650".format(self.ip),        
            'SAM': "{}:7656".format(self.ip),        
            'Webconsole': "http://{}:7070".format(self.ip),        
            'Proxies': {
                'HTTP': "{}:4444".format(self.ip),        
                'Socks': "{}:4447".format(self.ip),        
            },
        }
        self.control = i2pcontrol.I2PControl(self.URLS['Control'])

    def info(self):
        """Fetch info from i2pcontrol"""
        try:
            return self.control.request("RouterInfo", 
                    i2pcontrol.INFO_REQUEST)['result']
        except requests.exceptions.ConnectionError:
            return {}

    def info_str(self):
        """String with verbose i2pd info"""
        info = self.info()
        if not info:
            return "{}\t{}\tNOT READY".format(self.id, self.ip)

        return "\t".join([
            self.id, self.ip,
            i2pcontrol.STATUS[info["i2p.router.net.status"]],
            str(info["i2p.router.net.tunnels.successrate"]) + "%",
            "{}/{}".format(
                info["i2p.router.netdb.knownpeers"],
                info["i2p.router.netdb.activepeers"]
            ),
            "{}/{}".format(
                info["i2p.router.net.total.received.bytes"],
                info["i2p.router.net.total.sent.bytes"]
            ),
            str(info["i2p.router.net.tunnels.participating"]),
        ])

    def add_tunnel(self, name, options):
        """Add I2P tunnel"""
        args_str = ""
        for k, v in options.items():
            args_str += "{} = {}\n".format(k, v)

        cmd = '/bin/sh -c \'printf "\n[{}]\n{}\n"'.format(name, args_str) + \
            ' >> /home/i2pd/data/tunnels.conf\''
        self.container.exec_run(cmd)
        self.container.exec_run("kill -HUP 1")

    def tunnel_destinations(self):
        """Get b32 destinations"""
        destinations = []
        for x in self.container.logs().split(b"\r\n"):
            if b"New private keys file" in x:
                destinations.append(x.split(b" ")[-2].decode())
        return destinations


    def __str__(self):
        return "i2pd node: {}  IP: {}".format(self.id, self.ip)

class Pyseeder(object):
    """Pyseeder object"""

    def __init__(self, container, netname):
        self.container = container
        self.netname = netname
        self._url, self._cert = "", ""

    @property
    def url(self):
        """URL of https server"""
        if not self._url:
            self.container.reload()
            self._url = "https://{}:8443/".format(self.container.attrs[
                'NetworkSettings']['Networks'][self.netname]['IPAddress'])
        return self._url

    @property
    def cert(self):
        """certificate path"""
        if not self._cert:
            for m in self.container.attrs['Mounts']:
                if m['Destination'] == '/home/pyseeder/data':
                    self._cert = os.path.join(
                                m['Source'], 'data', 'test_at_mail.i2p.crt')

        return self._cert

class Testnet(object):
    """Testnet object"""

    I2PD_IMAGE = "i2pd"
    PYSEEDER_IMAGE = "pyseeder"
    NETNAME = 'i2pdtestnet'
    NODES = {}
    PYSEEDER = None
    DEFAULT_ARGS = " --nat=false --netid=7 --ifname=eth0 " \
                   " --i2pcontrol.enabled=true --i2pcontrol.address=0.0.0.0 "

    def __init__(self, docker_client):
        self.cli = docker_client

    def create_network(self):
        """Create isolated docker network"""
        self.net = self.cli.networks.create(self.NETNAME, driver="bridge",
                internal=True)

    def remove_network(self):
        """Remove docker network"""
        self.net.remove()

    def run_i2pd(self, args=None, with_cert=True):
        """Start i2pd"""
        i2pd_args = self.DEFAULT_ARGS
        if args: i2pd_args += args

        if with_cert:
            cont = self.cli.containers.run(self.I2PD_IMAGE, i2pd_args, 
                    network=self.NETNAME,
                    volumes=[
                    '{}:/i2pd_certificates/reseed/test_at_mail.i2p.crt'.format(
                                                        self.PYSEEDER.cert)],
                    detach=True, tty=True)
        else:
            cont = self.cli.containers.run(self.I2PD_IMAGE, i2pd_args,
                    network=self.NETNAME, detach=True, tty=True)
        self.NODES[cont.id[:12]] = I2pd(cont, self.NETNAME)
        return cont.id

    def remove_i2pd(self, cid):
        """Stop and remove i2pd"""
        try:
            node = self.NODES.pop(cid)
        except KeyError:
            return

        node.container.stop()
        node.container.remove()

    def init_floodfills(self, count=1):
        """Initialize floodfills for reseeding"""
        for x in range(count):
            self.run_i2pd(" --floodfill ", with_cert=False)

    def run_pyseeder(self):
        """Run reseed"""
        volumes = []
        for n in self.NODES.values():
            ri = os.path.join(n.container.attrs["Mounts"][0]["Source"],
                    "router.info")
            volumes.append('{}:/netDb/{}.dat'.format(ri, rand_string()))

        cont = self.cli.containers.run(self.PYSEEDER_IMAGE, volumes=volumes,
                network=self.NETNAME, detach=True, tty=True)
        self.PYSEEDER = Pyseeder(cont, self.NETNAME)

    def print_info(self):
        """Print testnet statistics"""
        if self.NODES:
            print("\t".join([
                "CONTAINER", "IP", "STATUS", "SUCC RATE", "PEERS K/A", 
                "BYTES S/R", "PART. TUNNELS"
            ]))

            for n in self.NODES.values():
                print(n.info_str())
        else:
            print("Testnet is not running")

    def stop(self):
        """Stop nodes and reseeder"""
        if self.PYSEEDER:
            self.PYSEEDER.container.stop()
            self.PYSEEDER.container.remove()
            self.PYSEEDER = None

        for n in self.NODES.values():
            n.container.stop()
            n.container.remove()

        self.NODES.clear()
