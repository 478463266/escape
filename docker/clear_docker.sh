#!/usr/bin/env bash

# Clear containers
sudo docker rm $(docker ps --no-trunc -aq)
# Clear imaged
sudo docker rmi $(docker images -q -f "dangling=true")
sudo docker rmi escape/mdo