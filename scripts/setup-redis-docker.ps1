# setup-redis-docker.ps1
# Redis Docker Desktop Setup Script for NovelWriter
# 
# This script:
# 1. Checks if Docker Desktop is installed and running
# 2. Creates Redis 7.x container with auto-restart
# 3. Verifies Redis connectivity
# 4. Logs all operations to .sisyphus\evidence\task-7-redis-setup.log

param(
    [switch]$ForceRecreate,  # Force recreation of existing container
    [switch]$SkipChecks      # Skip Docker Desktop checks (for CI/CD)
)

$ErrorActionPreference = "Stop"
$REDIS_CONTAINER_NAME = "redis-novelwriter"
$REDIS_IMAGE = "redis:7-alpine"
$REDIS_PORT = 6379
$LOG_FILE = Join-Path $PSScriptRoot "..\.sisyphus\evidence\task-7-redis-setup.log"
$EVIDENCE_DIR = Join-Path $PSScriptRoot "..\.sisyphus\evidence"

# Ensure evidence directory exists
if (-not (Test-Path $EVIDENCE_DIR)) {
    New-Item -ItemType Directory -Force -Path $EVIDENCE_DIR | Out-Null
}

# Initialize log file
$logContent = @()
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    $logContent += $logEntry
    Write-Host $logEntry
}

function Save-Log {
    $logContent | Out-File -FilePath $LOG_FILE -Encoding UTF8
    Write-Log "Log saved to: $LOG_FILE"
}

function Test-DockerDesktopInstalled {
    Write-Log "Checking if Docker Desktop is installed..."
    
    # Check if docker command exists
    try {
        $dockerVersion = docker --version 2>&1
        Write-Log "Docker found: $dockerVersion"
        return $true
    } catch {
        Write-Log "Docker Desktop is NOT installed" "ERROR"
        return $false
    }
}

function Test-DockerDesktopRunning {
    Write-Log "Checking if Docker Desktop daemon is running..."
    
    try {
        $dockerInfo = docker info 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Docker Desktop daemon is running"
            return $true
        } else {
            Write-Log "Docker Desktop daemon is NOT running" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Failed to connect to Docker daemon: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Show-DockerDesktopDownloadInfo {
    Write-Log "Docker Desktop Download Information" "WARN"
    Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║           Docker Desktop Installation Required               ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Docker Desktop is not installed or not running.             ║
║                                                               ║
║  Download Docker Desktop for Windows:                        ║
║  https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe
║                                                               ║
║  Installation Steps:                                         ║
║  1. Run the installer                                        ║
║  2. Follow the installation wizard                          ║
║  3. Restart your computer if prompted                       ║
║  4. Launch Docker Desktop                                    ║
║  5. Accept the license agreement                            ║
║  6. Wait for Docker Desktop to start                        ║
║                                                               ║
║  After installation, re-run this script:                    ║
║  .\scripts\setup-redis-docker.ps1                           ║
║                                                               ║
╚══════════════════════════════════════════════════════════════╝

"@
}

function Test-RedisContainerExists {
    Write-Log "Checking if Redis container already exists..."
    
    try {
        $container = docker ps -a --filter "name=$REDIS_CONTAINER_NAME" --format "{{.Names}}" 2>&1
        if ($container -eq $REDIS_CONTAINER_NAME) {
            Write-Log "Redis container '$REDIS_CONTAINER_NAME' already exists"
            return $true
        }
        Write-Log "Redis container does not exist"
        return $false
    } catch {
        Write-Log "Failed to check container status: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-RedisContainerRunning {
    Write-Log "Checking if Redis container is running..."
    
    try {
        $container = docker ps --filter "name=$REDIS_CONTAINER_NAME" --format "{{.Names}}" 2>&1
        if ($container -eq $REDIS_CONTAINER_NAME) {
            Write-Log "Redis container '$REDIS_CONTAINER_NAME' is running"
            return $true
        }
        Write-Log "Redis container is not running"
        return $false
    } catch {
        Write-Log "Failed to check container status: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Stop-RemoveRedisContainer {
    Write-Log "Stopping and removing existing Redis container..."
    
    try {
        docker stop $REDIS_CONTAINER_NAME 2>&1 | Out-Null
        Write-Log "Container stopped"
    } catch {
        Write-Log "Failed to stop container (may not be running): $($_.Exception.Message)" "WARN"
    }
    
    try {
        docker rm $REDIS_CONTAINER_NAME 2>&1 | Out-Null
        Write-Log "Container removed"
    } catch {
        Write-Log "Failed to remove container: $($_.Exception.Message)" "ERROR"
        throw
    }
}

function Create-RedisContainer {
    Write-Log "Creating Redis container..."
    Write-Log "Image: $REDIS_IMAGE"
    Write-Log "Container Name: $REDIS_CONTAINER_NAME"
    Write-Log "Port: $REDIS_PORT:6379"
    Write-Log "Restart Policy: unless-stopped"
    
    try {
        docker run -d `
            --name $REDIS_CONTAINER_NAME `
            -p ${REDIS_PORT}:6379 `
            --restart unless-stopped `
            $REDIS_IMAGE 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Redis container created successfully"
            return $true
        } else {
            Write-Log "Failed to create Redis container" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Failed to create Redis container: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Wait-ContainerReady {
    param(
        [int]$TimeoutSeconds = 30
    )
    
    Write-Log "Waiting for Redis container to be ready (timeout: ${TimeoutSeconds}s)..."
    
    $startTime = Get-Date
    while ($true) {
        $elapsed = (Get-Date) - $startTime
        if ($elapsed.TotalSeconds -gt $TimeoutSeconds) {
            Write-Log "Timeout waiting for container to be ready" "ERROR"
            return $false
        }
        
        try {
            $state = docker inspect $REDIS_CONTAINER_NAME --format "{{.State.Running}}" 2>&1
            if ($state -eq "True") {
                Write-Log "Container is running"
                return $true
            }
        } catch {
            # Container may not be ready yet
        }
        
        Start-Sleep -Seconds 2
    }
}

function Test-RedisConnection {
    Write-Log "Testing Redis connection..."
    
    try {
        # Try using docker exec first (most reliable)
        $response = docker exec $REDIS_CONTAINER_NAME redis-cli ping 2>&1
        if ($response -eq "PONG") {
            Write-Log "Redis connection successful: PONG"
            return $true
        } else {
            Write-Log "Redis responded with unexpected value: $response" "WARN"
        }
    } catch {
        Write-Log "Failed to ping Redis via docker exec: $($_.Exception.Message)" "WARN"
    }
    
    # Try using redis-cli directly if available
    try {
        $response = redis-cli -h localhost -p $REDIS_PORT ping 2>&1
        if ($response -eq "PONG") {
            Write-Log "Redis connection successful (via redis-cli): PONG"
            return $true
        }
    } catch {
        Write-Log "redis-cli not available or connection failed" "WARN"
    }
    
    # Try using PowerShell TCP connection
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect("localhost", $REDIS_PORT)
        if ($tcpClient.Connected) {
            Write-Log "Redis TCP connection successful on port $REDIS_PORT"
            $tcpClient.Close()
            return $true
        }
    } catch {
        Write-Log "Failed to connect to Redis via TCP: $($_.Exception.Message)" "ERROR"
    }
    
    return $false
}

function Get-ContainerInfo {
    Write-Log "Redis Container Information:"
    
    try {
        $info = docker inspect $REDIS_CONTAINER_NAME 2>&1 | ConvertFrom-Json
        if ($info) {
            Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║              Redis Container Information                     ║
╠══════════════════════════════════════════════════════════════╣

  Container Name: $($info[0].Name -replace '/', '')
  Image:          $($info[0].Config.Image)
  Status:         $($info[0].State.Status)
  Running:        $($info[0].State.Running)
  Ports:
    - Host: $REDIS_PORT -> Container: 6379
  Restart Policy: $($info[0].HostConfig.RestartPolicy.Name)
  Created:        $($info[0].Created)

╚══════════════════════════════════════════════════════════════╝

"@
        }
    } catch {
        Write-Log "Failed to get container info: $($_.Exception.Message)" "WARN"
    }
}

function Save-PingEvidence {
    param(
        [bool]$Success
    )
    
    $pingEvidenceFile = Join-Path $EVIDENCE_DIR "task-7-redis-ping.txt"
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    if ($Success) {
        "[$timestamp] Redis ping test: SUCCESS`nPONG" | Out-File -FilePath $pingEvidenceFile -Encoding UTF8
    } else {
        "[$timestamp] Redis ping test: FAILED`nConnection could not be established" | Out-File -FilePath $pingEvidenceFile -Encoding UTF8
    }
    
    Write-Log "Ping evidence saved to: $pingEvidenceFile"
}

# Main execution
Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║        NovelWriter Redis Docker Setup Script                 ║
╚══════════════════════════════════════════════════════════════╝

"@

try {
    # Check Docker Desktop installation
    if (-not $SkipChecks) {
        if (-not (Test-DockerDesktopInstalled)) {
            Show-DockerDesktopDownloadInfo
            Save-Log
            exit 1
        }
        
        if (-not (Test-DockerDesktopRunning)) {
            Write-Log "Docker Desktop is installed but not running" "ERROR"
            Write-Host @"

Please start Docker Desktop:
1. Open Docker Desktop from Start Menu
2. Wait for it to fully start (whale icon in system tray)
3. Re-run this script

"@
            Save-Log
            exit 1
        }
    } else {
        Write-Log "Skipping Docker Desktop checks (--SkipChecks flag set)"
    }
    
    # Check if container already exists
    $containerExists = Test-RedisContainerExists
    $containerRunning = Test-RedisContainerRunning
    
    if ($containerRunning -and -not $ForceRecreate) {
        Write-Log "Redis container is already running"
        Write-Log "Use --ForceRecreate to recreate the container"
    } else {
        # Remove existing container if needed
        if ($containerExists -and $ForceRecreate) {
            Stop-RemoveRedisContainer
        } elseif ($containerExists -and -not $containerRunning) {
            # Container exists but not running, remove it
            Write-Log "Container exists but not running, removing..."
            docker rm $REDIS_CONTAINER_NAME 2>&1 | Out-Null
        }
        
        # Create new container
        if (-not (Create-RedisContainer)) {
            Write-Log "Failed to create Redis container" "ERROR"
            Save-Log
            exit 1
        }
        
        # Wait for container to be ready
        if (-not (Wait-ContainerReady -TimeoutSeconds 30)) {
            Write-Log "Container failed to start" "ERROR"
            Save-Log
            exit 1
        }
    }
    
    # Verify Redis connection
    $connectionSuccess = Test-RedisConnection
    
    # Display container information
    Get-ContainerInfo
    
    # Save evidence
    Save-PingEvidence -Success $connectionSuccess
    
    # Save log
    Save-Log
    
    if ($connectionSuccess) {
        Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                    Setup Complete ✓                          ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Redis container is running and accessible                   ║
║                                                               ║
║  Quick Commands:                                             ║
║  - Connect:      docker exec -it $REDIS_CONTAINER_NAME redis-cli
║  - Stop:         docker stop $REDIS_CONTAINER_NAME
║  - Start:        docker start $REDIS_CONTAINER_NAME
║  - Logs:         docker logs $REDIS_CONTAINER_NAME
║  - Remove:       docker rm -f $REDIS_CONTAINER_NAME
║                                                               ║
║  Evidence saved to:                                          ║
║  - Setup Log:  $LOG_FILE
║  - Ping Test:  $(Join-Path $EVIDENCE_DIR "task-7-redis-ping.txt")
║                                                               ║
╚══════════════════════════════════════════════════════════════╝

"@
        exit 0
    } else {
        Write-Log "Setup completed but Redis connection test failed" "ERROR"
        Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║               Setup Complete with Errors ⚠                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Container is running but connection test failed             ║
║                                                               ║
║  Troubleshooting:                                            ║
║  1. Check container logs: docker logs $REDIS_CONTAINER_NAME
║  2. Verify port binding: docker port $REDIS_CONTAINER_NAME
║  3. Check firewall settings                                  ║
║                                                               ║
╚══════════════════════════════════════════════════════════════╝

"@
        exit 1
    }
} catch {
    Write-Log "Fatal error: $($_.Exception.Message)" "ERROR"
    Save-Log
    Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║                    Setup Failed ✗                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Error: $($_.Exception.Message)
║                                                               ║
║  Check the log file for details:                            ║
║  $LOG_FILE
║                                                               ║
╚══════════════════════════════════════════════════════════════╝

"@
    exit 1
}
