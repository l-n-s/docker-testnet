import argparse
import os
import sys
import time
import warnings
import logging
from pprint import pprint

import docker 

from testnet.testnet import Testnet

__version__ = "0.1"

class TestnetCtl(object):

    def __init__(self, testnet):
        self.testnet = testnet

    def start(self, args):
        """Start testnet"""
        if not self.testnet.NODES:
            self.testnet.create_network()
            cid = self.testnet.run_i2pd(floodfill=True, with_seed=False)
            time.sleep(5)
            self.testnet.make_seed(cid)
        print("*** Testnet is running")

    def status(self, args):
        """Display testnet statistics"""
        self.testnet.print_info()
        
    def stop(self, args):
        """Stop testnet"""
        if self.testnet.NODES:
            self.testnet.stop()
            self.testnet.remove_network()
        print("*** Testnet stopped")

    def add(self, args):
        """Add node(s) to testnet"""
        if not self.testnet.NODES: return

        for x in range(args.count):
            cid = self.testnet.run_i2pd(with_seed=True,
                    floodfill=args.floodfill)
            print(cid)

        print("*** Added {} nodes".format(args.count))

    def remove(self, args):
        """Remove node(s) from testnet"""
        for n in args.ids:
            self.testnet.remove_i2pd(n)
            print(n)

        print("*** Removed {} nodes".format(len(args.ids)))

    def inspect(self, args):
        """Show node information. Usage: inspect [id]"""
        try:
            node = self.testnet.NODES[args.cid]
        except KeyError:
            warnings.warn("No such container")
            return

        print("Container: {}\tIP: {}\n".format(node.id, node.ip))
        pprint(node.info())
        print("\nResources:\n")
        pprint(node.URLS)

    def create_tunnel(self, args):
        """Create I2P tunnel. Usage: create_tunnel [id] [name] [option=value] ..."""
        node = self.testnet.NODES[args.cid]
        options = {}
        for x in args.options:
            k, v = x.split("=")
            options[k] = v

        node.add_tunnel(args.name, options)
        time.sleep(1)
        print("*** Tunnel created: {}".format(node.tunnel_destinations()[-1]))

log = logging.getLogger(__name__)

def main():
    cli = docker.DockerClient(base_url='unix://var/run/docker.sock', 
            version='auto')
    testnetctl = TestnetCtl(Testnet(cli))

    if os.getenv("I2PD_IMAGE"):
        testnetctl.testnet.I2PD_IMAGE = os.getenv("I2PD_IMAGE")
    if os.getenv("NETNAME"):
        testnetctl.testnet.NETNAME = os.getenv("NETNAME")
    if os.getenv("DEFAULT_ARGS"):
        testnetctl.testnet.DEFAULT_ARGS = os.getenv("DEFAULT_ARGS")

    parser = argparse.ArgumentParser()
    parser.add_argument('--loglevel', default=logging.INFO, help="Log level",
            choices=[logging.CRITICAL, logging.ERROR, logging.WARNING,
                     logging.INFO, logging.DEBUG])

    subparsers = parser.add_subparsers(title="actions",help="Command to execute")

    start_parser = subparsers.add_parser("start", description="Start a testnet")
    start_parser.set_defaults(func=testnetctl.start)

    stop_parser = subparsers.add_parser("stop", description="Stop the testnet")
    stop_parser.set_defaults(func=testnetctl.stop)

    status_parser = subparsers.add_parser("status", description="Show status")
    status_parser.set_defaults(func=testnetctl.status)

    add_nodes_parser = subparsers.add_parser("add", description="Add i2pd nodes")
    add_nodes_parser.add_argument('count', type=int, help="Number of nodes to add")
    add_nodes_parser.add_argument('--floodfill', action="store_true", help="Setup floodfill nodes")
    add_nodes_parser.set_defaults(func=testnetctl.add)

    remove_nodes_parser = subparsers.add_parser("remove", description="Remove specified i2pd nodes")
    remove_nodes_parser.add_argument('ids', nargs='*', help="Nodes to remove")
    remove_nodes_parser.set_defaults(func=testnetctl.remove)

    inspect_nodes_parser = subparsers.add_parser("inspect", description="Show info about a node")
    inspect_nodes_parser.add_argument('cid', help="Node id")
    inspect_nodes_parser.set_defaults(func=testnetctl.inspect)

    create_tunnel_parser = subparsers.add_parser("create_tunnel", 
            description="Create a new tunnel at the specified node")
    create_tunnel_parser.add_argument('cid', help="Node id")
    create_tunnel_parser.add_argument('name', help="Tunnel name")
    create_tunnel_parser.add_argument('options', nargs='*', 
            help="tunnels.conf options in form of option=value option2=value2 ...")
    create_tunnel_parser.set_defaults(func=testnetctl.create_tunnel)

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel, format='%(levelname)-8s %(message)s')

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
