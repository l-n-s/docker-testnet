import os
import time
import warnings
from pprint import pprint

import docker 

from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.contrib.completers import WordCompleter


from testnet.testnet import Testnet

__version__ = "0.1"

history = InMemoryHistory()
TestnetCompleter = WordCompleter(['help', 'quit', 'start', 'stats', 'stop',
    'add', 'create_tunnel', 'remove', 'inspect'])


def start(testnet):
    """Start testnet"""
    if not testnet.NODES:
        testnet.create_network()
        testnet.init_floodfills()
        time.sleep(5)
        testnet.make_seed()
    print("*** Testnet is running")

def stats(testnet):
    """Display testnet statistics"""
    testnet.print_info()
    
def stop(testnet):
    """Stop testnet"""
    if testnet.NODES:
        testnet.stop()
        testnet.remove_network()
    print("*** Testnet stopped")

def add(testnet, count=1, floodfill=False):
    """Add node(s) to testnet. Usage: add [count=1] [floodfill=False]"""
    if not testnet.NODES: return
    count, floodfill = int(count), bool(floodfill)
    args = " --reseed.zipfile=/seed.zip "

    if floodfill: args += " --floodfill "

    for x in range(count):
        cid = testnet.run_i2pd(args)
        print(cid[:12])

    print("*** Added {} nodes".format(count))

def create_tunnel(testnet, cid, name, args):
    """Create I2P tunnel. Usage: create_tunnel [id] [name] [option=value] ..."""
    node = testnet.NODES[cid]
    options = {}
    for x in args:
        k, v = x.split("=")
        options[k] = v

    node.add_tunnel(name, options)
    time.sleep(1)
    print("*** Tunnel created: {}".format(node.tunnel_destinations()[-1]))

def remove(testnet, ids):
    """Remove node(s) from testnet. Usage: remove [id] ..."""
    for n in ids:
        testnet.remove_i2pd(n)
        print(n)

    print("*** Removed {} nodes".format(len(ids)))

def inspect(testnet, cid):
    """Show node information. Usage: inspect [id]"""
    try:
        node = testnet.NODES[cid]
    except KeyError:
        warnings.warn("No such container")
        return

    print("Container: {}\tIP: {}\n".format(node.id, node.ip))
    pprint(node.info())
    print("\nResources:\n")
    pprint(node.URLS)

def print_help():
    """Print help"""
    print("Docker based i2pd testnet v{}\n\nCommands:".format(__version__))
    print("""
    help\t{}
    start\t{}
    stats\t{}
    stop\t{}
    add \t{}
    create_tunnel \t{}
    remove \t{}
    inspect \t{}
    quit\tStop testnet and quit
    """.format(
        print_help.__doc__, 
        start.__doc__, 
        stats.__doc__,
        stop.__doc__, 
        add.__doc__,
        create_tunnel.__doc__,
        remove.__doc__,
        inspect.__doc__,)
    )

def main():
    # cli = docker.from_env()
    cli = docker.DockerClient(base_url='unix://var/run/docker.sock', 
            version='auto')
    testnet = Testnet(cli)

    if os.getenv("I2PD_IMAGE"):
        testnet.I2PD_IMAGE = os.getenv("I2PD_IMAGE")
    if os.getenv("NETNAME"):
        testnet.NETNAME = os.getenv("NETNAME")
    if os.getenv("DEFAULT_ARGS"):
        testnet.DEFAULT_ARGS = os.getenv("DEFAULT_ARGS")

    while 1:
        try:
            inpt = prompt('testnet> ', history=history, 
                    auto_suggest=AutoSuggestFromHistory(),
                    completer=TestnetCompleter)
            if not inpt: continue
        except (EOFError, KeyboardInterrupt):
            if testnet.NODES:
                warnings.warn("Testnet containers are still running")
            break

        command = inpt.split()

        if command[0]   == "help":
            print_help()
        elif command[0] == "stop" or command[0] == "quit":
            stop(testnet)
            if command[0] == "quit": break
        elif command[0] == "start":
            start(testnet)
        elif command[0] == "stats":
            stats(testnet)
        elif command[0] == "add":
            args = command[1:] if len(command) > 1 else []
            add(testnet, *args)
        elif command[0] == "create_tunnel":
            if len(command) < 7: continue
            create_tunnel(testnet, command[1], command[2], command[3:])
        elif command[0] == "remove":
            if len(command) < 2: continue
            remove(testnet, command[1:])
        elif command[0] == "inspect":
            if len(command) != 2: continue
            inspect(testnet, command[1])
        elif command[0] == "root":
            import pdb; pdb.set_trace() 


if __name__ == "__main__":
    main()
