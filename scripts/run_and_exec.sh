#!/bin/bash

docker-compose up --build -d app

# Get the container ID by name
container_id=$(docker ps -qf "name=inv_test_app_1")

# Check if the container exists
if [ -z "$container_id" ]; then
    echo "Container inv_test_app_1 not found."
    exit 1
fi

# Execute /bin/bash inside the container
docker exec -it "$container_id" /bin/bash
