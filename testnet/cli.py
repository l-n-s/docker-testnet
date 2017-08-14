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
    'add', 'remove', 'inspect'])


def start(testnet):
    """Start testnet"""
    testnet.create_network()
    testnet.init_floodfills()
    testnet.run_pyseeder()
    print("*** Testnet is running")

def stats(testnet):
    """Display testnet statistics"""
    testnet.print_info()
    
def stop(testnet):
    """Stop testnet"""
    testnet.stop()
    testnet.remove_network()
    print("*** Testnet stopped")

def add(testnet, count=1, floodfill=False):
    """Add node(s) to testnet. Usage: add [count=1] [floodfill=False]"""
    count, floodfill = int(count), bool(floodfill)
    args = " --reseed.urls={} ".format(testnet.RESEED_URL)

    if floodfill: args += " --floodfill "

    for x in range(count):
        cid = testnet.run_i2pd(args)
        print(cid[:12])

    print("*** Added {} nodes".format(count))

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
    remove \t{}
    inspect \t{}
    quit\tStop testnet and quit
    """.format(
        print_help.__doc__, 
        start.__doc__, 
        stats.__doc__,
        stop.__doc__, 
        add.__doc__,
        remove.__doc__,
        inspect.__doc__,)
    )

def main():
    # cli = docker.from_env()
    cli = docker.DockerClient(base_url='unix://var/run/docker.sock', 
            version='auto')
    testnet = Testnet(cli)

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

        if command[0]       == "help":
            print_help()
        elif command[0]     == "stop" or command[0] == "quit":
            if testnet.NODES: stop(testnet)
            if command[0] == "quit": break
        elif command[0]     == "start":
            if not testnet.NODES: start(testnet)
        elif testnet.NODES:
            if command[0]   == "stats":
                stats(testnet)
            elif command[0] == "add":
                args = command[1:] if len(command) > 1 else []
                add(testnet, *args)
            elif command[0] == "remove":
                if len(command) < 2: continue
                remove(testnet, command[1:])
            elif command[0] == "inspect":
                if len(command) != 2: continue
                inspect(testnet, command[1])

if __name__ == "__main__":
    main()
