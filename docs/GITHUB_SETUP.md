# GitHub Repository Security

## Repository

- **URL:** https://github.com/bolagnaise/tesla-sync
- **Docker Hub:** https://hub.docker.com/r/bolagnaise/tesla-sync

## Protected Files (via .gitignore)

These files are excluded from version control:

| File | Contains |
|------|----------|
| `.env` | API keys, secrets, credentials |
| `data/app.db` | User database |
| `data/.fernet_key` | Encryption key |
| `*.db`, `*.sqlite` | Any database files |
| `venv/` | Python virtual environment |
| `__pycache__/` | Python bytecode |
| `.DS_Store` | macOS system files |

## Safe to Commit

| File | Purpose |
|------|---------|
| `.env.example` | Template with placeholder values |
| Source code | All `.py`, `.html`, `.js` files |
| Documentation | All `.md` files |
| Docker config | `Dockerfile`, `docker-compose.yml` |
| Migrations | Database schema (no data) |

## Clone and Deploy

```bash
git clone https://github.com/bolagnaise/tesla-sync.git
cd tesla-sync

# Create .env from template
cp .env.example .env

# Edit with your credentials (or use web UI after first run)
nano .env

# Start with Docker
docker-compose up -d
```

## If You Accidentally Commit Secrets

1. **Immediately rotate** any exposed credentials
2. Use BFG Repo-Cleaner or `git filter-branch` to remove from history
3. Force push the cleaned history
4. See: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository

## Required GitHub Secrets

For CI/CD automation (Settings → Secrets → Actions):

| Secret | Purpose |
|--------|---------|
| `DOCKER_HUB_TOKEN` | Docker Hub access token for image publishing |
| `DISCORD_WEBHOOK` | (Optional) Discord notifications on deploy |
