# Docker Hub CI/CD Pipeline

Automated Docker image builds via GitHub Actions.

## Overview

Every push to `main` automatically:
- Builds multi-architecture images (amd64, arm64)
- Pushes to Docker Hub with appropriate tags
- Updates Docker Hub README from repository README
- Sends Discord notification (if webhook configured)

## Image Locations

| Repository | Status |
|------------|--------|
| `bolagnaise/tesla-sync` | **Primary** - Use this |
| `bolagnaise/tesla-amber-sync` | Legacy (deprecated) |

## Tags

| Tag | Description |
|-----|-------------|
| `latest` | Most recent main branch build |
| `main` | Same as latest |
| `v1.0.0` | Specific version (from git tags) |
| `abc1234` | Short commit SHA |

## Quick Deploy

```bash
docker run -d \
  --name tesla-sync \
  -p 5001:5001 \
  -v ./data:/app/data \
  -e SECRET_KEY=your-random-secret-key \
  --restart unless-stopped \
  bolagnaise/tesla-sync:latest
```

> **Note:** Encryption key is auto-generated on first run and saved to `./data/.fernet_key`

## GitHub Secrets Required

Configure in repository Settings → Secrets → Actions:

| Secret | Required | Purpose |
|--------|----------|---------|
| `DOCKER_HUB_TOKEN` | Yes | Docker Hub access token |
| `DISCORD_WEBHOOK` | No | Discord notifications |

### Creating Docker Hub Token

1. Log in to https://hub.docker.com
2. Profile → Account Settings → Security → Access Tokens
3. New Access Token with **Read, Write, Delete** permissions
4. Copy token and add as `DOCKER_HUB_TOKEN` secret

## Workflow Features

The workflow (`.github/workflows/docker-publish.yml`) includes:

- **Multi-platform builds:** linux/amd64, linux/arm64
- **Build caching:** Registry-based cache for faster builds
- **Semantic versioning:** Git tags create version tags (v1.0.0 → 1.0.0, 1.0, 1)
- **PR builds:** Builds but doesn't push (validation only)
- **Manual trigger:** Can be run manually via Actions tab
- **Discord notifications:** Posts to Discord on successful deploy

## Creating a Release

```bash
# Tag the release
git tag v1.2.0
git push origin v1.2.0
```

This creates Docker tags:
- `bolagnaise/tesla-sync:1.2.0`
- `bolagnaise/tesla-sync:1.2`
- `bolagnaise/tesla-sync:1`
- `bolagnaise/tesla-sync:latest`

## Update Users' Containers

### Manual Update

```bash
docker pull bolagnaise/tesla-sync:latest
docker restart tesla-sync
```

### Automatic Updates (Watchtower)

```bash
docker run -d \
  --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  tesla-sync \
  --interval 3600 \
  --cleanup
```

## Troubleshooting

### Build Fails

1. Check Actions tab for error logs
2. Common issues:
   - Missing `DOCKER_HUB_TOKEN` secret
   - Dockerfile syntax error
   - Network timeout (retry usually works)

### Image Not Updating

```bash
# Force pull latest
docker pull bolagnaise/tesla-sync:latest

# Check image digest
docker images --digests bolagnaise/tesla-sync
```

### Discord Notification Not Working

- Verify `DISCORD_WEBHOOK` secret is set
- Check webhook URL is valid
- Webhook failures don't fail the build

## Architecture

```
Push to main
     │
     ▼
GitHub Actions
     │
     ├─► Build amd64 image
     ├─► Build arm64 image
     │
     ▼
Docker Hub
     │
     ├─► bolagnaise/tesla-sync:latest
     └─► bolagnaise/tesla-sync:main

Discord ◄── Notification
```
