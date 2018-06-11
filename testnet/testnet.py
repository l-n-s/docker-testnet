import os
import random
import string
import tarfile
import zipfile
import tempfile
import time

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
                    i2pcontrol.INFO_METHODS["RouterInfo"])['result']
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


class Testnet(object):
    """Testnet object"""

    I2PD_IMAGE = "purplei2p/i2pd"
    NETNAME = 'i2pdtestnet'
    NODES = {}
    DEFAULT_ARGS = " --nat=false --netid=7 --ifname=eth0 " \
                   " --i2pcontrol.enabled=true --i2pcontrol.address=0.0.0.0 "
    SEED_FILE = os.path.join(tempfile.gettempdir(), 'seed.zip')

    def __init__(self, docker_client):
        self.cli = docker_client

        for cont in self.cli.containers.list(filters={"label": "i2pd"}):
            self.NODES[cont.id[:12]] = I2pd(cont, self.NETNAME)

    def create_network(self):
        """Create isolated docker network"""
        self.cli.networks.create(self.NETNAME, driver="bridge", internal=True)

    def remove_network(self):
        """Remove docker network"""
        self.cli.networks.get(self.NETNAME).remove()

    def run_i2pd(self, args=None, with_seed=True, floodfill=False):
        """Start i2pd"""
        i2pd_args, labels = self.DEFAULT_ARGS, ["i2pd"]
        if args: i2pd_args += args

        if floodfill:
            i2pd_args += " --floodfill "
            labels += ["floodfill"]

        if with_seed:
            i2pd_args += " --reseed.zipfile=/seed.zip "
            cont = self.cli.containers.run(self.I2PD_IMAGE, i2pd_args,
                    volumes=["{}:/seed.zip".format(self.SEED_FILE)],
                    labels=labels, network=self.NETNAME, detach=True, tty=True)
        else:
            labels += ["noseed"]
            cont = self.cli.containers.run(self.I2PD_IMAGE, i2pd_args,
                    labels=labels, network=self.NETNAME, detach=True, tty=True)
        self.NODES[cont.id[:12]] = I2pd(cont, self.NETNAME)
        return cont.id[:12]

    def remove_i2pd(self, cid):
        """Stop and remove i2pd"""
        try:
            node = self.NODES.pop(cid)
        except KeyError:
            return

        node.container.stop()
        node.container.remove()

    def make_seed(self, cid):
        """creates a zip reseed file"""
        ri_path = "/home/i2pd/data/router.info"

        with tempfile.TemporaryFile() as fp:
            while True:
                try:
                    arc_data = self.NODES[cid].container.get_archive(ri_path)[0].read()
                    break
                except:
                    time.sleep(0.1)

            fp.write(arc_data)
            fp.seek(0)
            ri_file = tarfile.open(fileobj=fp, mode='r:')\
                    .extractfile("router.info").read()
            tf = tempfile.mkstemp()[1]
            with open(tf, 'wb') as f: f.write(ri_file)
            zf = zipfile.ZipFile(self.SEED_FILE, "w")
            zf.write(tf, "ri.dat")
            zf.close()
            os.remove(tf)

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
        for n in self.NODES.values():
            n.container.stop()
            n.container.remove()

        os.remove(self.SEED_FILE)
        self.NODES.clear()
