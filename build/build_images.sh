#!/bin/bash
directory=$(dirname $(readlink -f $0))

cd $directory/i2pd_docker
docker build -t i2pd --build-arg GIT_BRANCH=openssl .

cd $directory/pyseeder_docker
docker build -t pyseeder .

echo "*** Images build completed"
