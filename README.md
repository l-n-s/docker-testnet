docker testnet
==============

Run and manage your own local [I2P network](http://i2pd.website) with Docker.


Installing
----------

Install requirements and add your user to docker group ([security notes](https://docs.docker.com/engine/installation/linux/linux-postinstall/)):

    sudo apt install docker.io python3 python3-venv
    sudo gpasswd -a your-user docker

Pull docker image:

    sudo docker pull purplei2p/i2pd 

Clone the repo: 
    
    git clone https://github.com/l-n-s/docker-testnet && cd docker-testnet

Create virtual environment and install:

    python3 -m venv venv && source venv/bin/activate
    pip install .


Usage
-----

Read help message:

    testnetctl -h
    
Start a network: 

    testnetctl start

Or you may want to start a network with some nodes and floodfills:

    testnetctl start --nodes 10 --floodfills 5

Add 5 floodfill nodes and 10 regular nodes:

    testnetctl add 5 --floodfill
    testnetctl add 10

Show network statistics overview:

    testnetctl status

Show individual node information:

    testnetctl inspect d34db33f1001
    
Remove couple of nodes:

    testnetctl remove d34db33f1001 3f1001d34db3

Create I2P tunnel (options are specified exactly as `key=value` without spaces):

    testnetctl create_tunnel d34db33f1001 test-tunnel type=http host=127.0.0.1 port=8888 keys=test.dat

Stop a network and quit:

    testnetctl stop


Configuration
-------------

Takes environment variables for configuration:

    I2PD_IMAGE   -  docker image to use
    NETNAME      -  docker network name
    DEFAULT_ARGS -  default arguments for binary

