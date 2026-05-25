---
name: docker-helper
description: Help users write and debug Dockerfiles and docker-compose configurations. Use when the user needs help with containerization, Docker builds, or container orchestration.
---

# Docker Helper

## When to use

Use for Dockerfile design, compose layout, image hygiene, and quick inspection of a running container.

## Debugging script

For a given container ID or name, run [`scripts/docker_debug.sh`](scripts/docker_debug.sh):

```bash
./scripts/docker_debug.sh <container_id_or_name>
```

It prints recent logs, a short inspect summary, and one non-streaming `docker stats` sample. For an interactive shell inside the container, use `docker exec -it <container_id_or_name> /bin/sh` (or `/bin/bash` if available).

## Dockerfile best practices

1. Use multi-stage builds to reduce image size.
2. Pin base image versions (for example `node:20-alpine`, not `node:latest`).
3. Run as a non-root user where possible.
4. Use `.dockerignore` to exclude unnecessary build context.
5. Order layers from least to most frequently changed.

## Example Dockerfile (Node.js)

Illustrative multi-stage layout: build in a `builder` stage, copy artifacts and production dependencies into a slim runtime stage, run as non-root, expose the app port.

## Docker Compose

Typical pattern: an `app` service `build: .`, `ports`, `environment`, `depends_on` a database; database service with a named volume and secrets-friendly env (for example `POSTGRES_PASSWORD_FILE`).

## Manual commands

- `docker logs <container_id>`
- `docker exec -it <container_id> /bin/sh`
- `docker inspect <container_id>`
- `docker stats`
