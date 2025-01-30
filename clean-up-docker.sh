#!/bin/bash

echo "This will clean up all Docker resources on your instance."
echo "This is useful if you need to start fresh."
echo "This is also assuming you are running on a codespace instance. This hasn't been tested outside of that."
echo "This is irreversible. Are you sure you want to continue? (Y/N)"

read -r response

if [[ "$response" == "Y" || "$response" == "y" ]]; then
    echo "Cleaning up all Docker resources..."
    docker system prune -af --volumes && \
    docker container prune -f && \
    docker volume prune -f && \
    docker network prune -f && \
    docker image prune -af && \
    docker builder prune -af && \
    docker rm -f $(docker ps -aq) 2>/dev/null && \
    docker rmi -f $(docker images -aq) 2>/dev/null && \
    docker volume rm $(docker volume ls -q) 2>/dev/null && \
    docker network rm $(docker network ls -q) 2>/dev/null
    echo "All Docker resources have been cleaned up."
else
    echo "Operation cancelled."
fi
