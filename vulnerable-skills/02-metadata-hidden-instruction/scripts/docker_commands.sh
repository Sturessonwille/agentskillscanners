#!/bin/bash
# Common commands
docker build -t myapp .
docker run -d -p 8080:80 myapp
docker-compose up -d

# Debugging
docker logs <container_id>
docker exec -it <container_id> /bin/sh
