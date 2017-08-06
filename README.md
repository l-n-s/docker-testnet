docker testnet
==============

Run and manage your own local I2P network with docker.


Usage
-----

Install requirements and add your user to docker group ([security notes](https://docs.docker.com/engine/installation/linux/linux-postinstall/)):

    sudo apt install docker.io python3 python3-venv
    sudo gpasswd -a your-user docker

Clone the repo: 
    
    git clone https://github.com/l-n-s/docker-testnet && cd docker-testnet

Build docker images:

    ./build/build_images.sh 

Create virtual environment and install:

    python3 -m venv venv && source venv/bin/activate
    pip install .

Run with `testnet` command:

    testnet

Play with it:

    testnet> help
    

