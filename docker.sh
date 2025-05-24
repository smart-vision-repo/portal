#!/bin/sh

# Display usage information if no arguments provided or help is requested
if [ $# -eq 0 ] || [ "$1" = "help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [command]"
    echo "Commands:"
    echo "  build    - Build Docker image for Smart Vision portal"
    echo "  run      - Run or restart the Smart Vision container"
    echo "  stop     - Stop the Smart Vision container"
    echo "  rm       - Delete the Smart Vision container"
    echo "  purge    - Remove Smart Vision container and image"
    echo "  help|-h  - Show this help message"
    exit 0
fi

if [ "$1" = "purge" ]; then
    docker ps -a | grep smart-vision-portal | awk '{print "docker rm " $1}' | sh
    docker rmi smart-vision-portal
    exit 0
elif [ "$1" = "run" ]; then
    # Check if container exists
    if docker ps -a | grep -q smart-vision-portal; then
        # If exists, restart it
        docker restart $(docker ps -a | grep smart-vision-portal | awk '{print $1}')
    else
        # If doesn't exist, create new container
        if [ "$(uname)" = "Linux" ]; then
            docker run -it --env-file /opt/bash/env -v /app:./ -v /var/tmp/smart-vision:/var/tmp/smart-vision -v /opt/models/yolo:/opt/models/yolo -p 8501:8501 --gpus '"device=0"' smart-vision/portal
        else
            docker run -it --env-file /opt/bash/env -v /app:./ -v /var/tmp/smart-vision:/var/tmp/smart-vision -v /opt/models/yolo:/opt/models/yolo -p 8501:8501 smart-vision-portal:
        fi
    fi
    exit 0
elif [ "$1" = "build" ]; then
    docker ps -a | grep smart-vision-portal | awk '{print "docker rm " $1}' | sh
    docker rmi smart-vision-portal
    docker build -t smart-vision-portal .
    exit 0
elif [ "$1" = "stop" ]; then
    docker ps -a | grep smart-vision-portal | awk '{print "docker stop " $1}' | sh
elif [ "$1" = "rm" ]; then
    docker ps -a | grep smart-vision-portal | awk '{print "docker rm " $1}' | sh
fi
