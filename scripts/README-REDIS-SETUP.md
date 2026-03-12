# Redis Docker Setup Guide

This guide explains how to set up Redis using Docker Desktop for the NovelWriter project.

## Quick Start

### Prerequisites

- Windows 10/11
- Administrator privileges (for Docker Desktop installation)
- Internet connection (to download Docker Desktop and Redis image)

### Step 1: Check Docker Desktop Installation

Run the setup script:

```powershell
.\scripts\setup-redis-docker.ps1
```

If Docker Desktop is not installed, the script will display download information.

### Step 2: Install Docker Desktop (if needed)

1. Download Docker Desktop for Windows:
   ```
   https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
   ```

2. Run the installer and follow the wizard

3. Restart your computer if prompted

4. Launch Docker Desktop from the Start Menu

5. Accept the license agreement

6. Wait for Docker Desktop to fully start (whale icon in system tray should be stable)

### Step 3: Run the Setup Script

```powershell
# Open PowerShell in the project root
.\scripts\setup-redis-docker.ps1
```

The script will:
- Verify Docker Desktop is installed and running
- Create a Redis 7.x container named `redis-novelwriter`
- Configure port mapping (6379:6379)
- Set restart policy to `unless-stopped`
- Verify Redis connectivity
- Save logs and evidence

### Step 4: Verify Installation

The script automatically verifies Redis connectivity. You should see:

```
╔══════════════════════════════════════════════════════════════╗
║                    Setup Complete ✓                          ║
╚══════════════════════════════════════════════════════════════╝

Redis container is running and accessible
```

Manual verification:

```powershell
# Check container status
docker ps --filter "name=redis-novelwriter"

# Test Redis connection
docker exec -it redis-novelwriter redis-cli ping

# Expected output: PONG
```

## Script Options

### Force Recreate

To recreate the Redis container (useful for resetting):

```powershell
.\scripts\setup-redis-docker.ps1 -ForceRecreate
```

### Skip Docker Checks

For CI/CD environments where Docker is guaranteed to be running:

```powershell
.\scripts\setup-redis-docker.ps1 -SkipChecks
```

## Container Details

| Property | Value |
|----------|-------|
| Container Name | `redis-novelwriter` |
| Image | `redis:7-alpine` |
| Port Mapping | `6379:6379` |
| Restart Policy | `unless-stopped` |
| Persistent Storage | No (in-memory only) |

## Common Commands

### Connect to Redis CLI

```powershell
docker exec -it redis-novelwriter redis-cli
```

### View Container Logs

```powershell
docker logs redis-novelwriter
```

### Stop Container

```powershell
docker stop redis-novelwriter
```

### Start Container

```powershell
docker start redis-novelwriter
```

### Remove Container

```powershell
docker rm -f redis-novelwriter
```

### View Container Details

```powershell
docker inspect redis-novelwriter
```

## Troubleshooting

### Docker Desktop Not Running

**Error**: `failed to connect to the docker API`

**Solution**:
1. Open Docker Desktop from Start Menu
2. Wait for the whale icon in system tray to become stable
3. Re-run the setup script

### Port Already in Use

**Error**: `Bind for 0.0.0.0:6379 failed: port is already allocated`

**Solution**:
1. Find the process using port 6379:
   ```powershell
   netstat -ano | findstr :6379
   ```
2. Stop the conflicting process or use a different port:
   ```powershell
   docker run -d --name redis-novelwriter -p 6380:6379 redis:7-alpine
   ```

### Container Won't Start

**Check logs**:
```powershell
docker logs redis-novelwriter
```

**Remove and recreate**:
```powershell
docker rm -f redis-novelwriter
.\scripts\setup-redis-docker.ps1
```

### Connection Refused

**Check if container is running**:
```powershell
docker ps --filter "name=redis-novelwriter"
```

**Verify port binding**:
```powershell
docker port redis-novelwriter
```

**Check Windows Firewall**:
- Ensure port 6379 is not blocked
- Docker Desktop should automatically configure firewall rules

## Evidence and Logs

The setup script saves evidence files:

- **Setup Log**: `.sisyphus\evidence\task-7-redis-setup.log`
  - Complete log of all operations
  - Timestamps and error messages
  - Container information

- **Ping Test**: `.sisyphus\evidence\task-7-redis-ping.txt`
  - Redis connectivity test result
  - Expected content: `PONG`

## Integration with NovelWriter

The Redis container is configured to work with the NovelWriter backend. To use Redis in your application:

```python
# Connection string
REDIS_URL = "redis://localhost:6379/0"

# Example usage with redis-py
import redis
r = redis.Redis(host='localhost', port=6379, db=0)
r.ping()  # Should return True
```

## Security Considerations

- Redis is exposed only on localhost (port 6379)
- No authentication is configured (for development use)
- For production, consider:
  - Adding Redis authentication (`requirepass`)
  - Using Docker networks for isolation
  - Enabling TLS encryption

## Uninstall

To completely remove Redis:

```powershell
# Stop and remove container
docker rm -f redis-novelwriter

# Remove Redis image
docker rmi redis:7-alpine

# Remove evidence files (optional)
Remove-Item -Recurse -Force .sisyphus\evidence
```

## References

- [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- [Redis Docker Official Image](https://hub.docker.com/_/redis)
- [Redis Documentation](https://redis.io/documentation)
