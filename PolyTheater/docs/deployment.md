# 部署文档

## 目录

- [环境要求](#环境要求)
- [快速部署](#快速部署)
- [详细配置](#详细配置)
- [生产环境部署](#生产环境部署)
- [监控与日志](#监控与日志)
- [故障排查](#故障排查)

---

## 环境要求

### 必需软件

- **Docker**: 20.10+ 
- **Docker Compose**: 2.0+
- **Git**: 用于克隆项目

### 资源要求

| 组件 | CPU | 内存 | 存储 |
|------|-----|------|------|
| Backend | 1核 | 512MB | 1GB |
| Frontend | 0.5核 | 256MB | 100MB |
| **总计** | **1.5核** | **768MB** | **1.1GB** |

### 外部服务

- **LLM API**: OpenAI 或兼容的 API 服务
- **Zep Cloud**: 知识图谱服务（可选）

---

## 快速部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd PolyTheater
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 编辑环境变量
nano backend/.env
```

**必需配置**:

```bash
# LLM API 配置
LLM_API_KEY=your-openai-api-key
LLM_BASE_URL=https://api.openai.com/v1  # 或其他兼容 API
LLM_MODEL_NAME=gpt-4o-mini

# Zep Cloud 配置（可选）
ZEP_API_KEY=your-zep-api-key

# Flask 配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=false
```

### 3. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4. 验证部署

```bash
# 检查后端健康状态
curl http://localhost:5001/health

# 检查前端
curl http://localhost:80
```

访问 **http://localhost** 开始使用。

---

## 详细配置

### 后端配置

#### 环境变量说明

| 变量 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `LLM_API_KEY` | LLM API密钥 | - | ✅ |
| `LLM_BASE_URL` | LLM API地址 | - | ✅ |
| `LLM_MODEL_NAME` | 使用的模型 | `gpt-4o-mini` | ❌ |
| `ZEP_API_KEY` | Zep Cloud密钥 | - | ❌ |
| `FLASK_HOST` | 监听地址 | `0.0.0.0` | ❌ |
| `FLASK_PORT` | 监听端口 | `5001` | ❌ |
| `FLASK_DEBUG` | 调试模式 | `false` | ❌ |
| `DEFAULT_MAX_ROUNDS` | 最大轮数 | `144` | ❌ |
| `DEFAULT_MINUTES_PER_ROUND` | 每轮分钟数 | `60` | ❌ |
| `CORS_ORIGINS` | CORS 允许的源 | `http://localhost:3000,http://localhost:5173` | ❌ |

#### 持久化存储

上传文件存储在 `./backend/uploads` 目录，已映射到容器内。

### 前端配置

#### Nginx配置

前端使用 Nginx 提供：

- 静态文件服务
- Vue Router history模式支持
- API反向代理
- Gzip压缩
- 静态资源缓存

自定义配置：编辑 `frontend/nginx.conf`

### 网络配置

#### 端口映射

| 服务 | 容器端口 | 主机端口 |
|------|----------|----------|
| Frontend | 80 | 80 |
| Backend | 5001 | 5001 |

#### 自定义端口

修改 `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "8080:80"  # 改为8080端口
  
  backend:
    ports:
      - "5002:5001"  # 改为5002端口
```

---

## 生产环境部署

### CORS 配置

CORS（跨域资源共享）配置用于控制前端可以访问后端 API 的源。

#### 开发环境

默认配置已包含开发环境常用的源：

```bash
# .env 文件
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

- `http://localhost:3000` - React 开发服务器
- `http://localhost:5173` - Vite 开发服务器

#### 生产环境

**重要**：生产环境应严格限制允许的源：

```bash
# .env 文件
CORS_ORIGINS=https://yourdomain.com
```

多个源使用逗号分隔：

```bash
CORS_ORIGINS=https://example.com,https://app.example.com
```

### HTTPS 配置

```nginx
# /etc/nginx/sites-available/polytheater
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

#### 使用Traefik

```yaml
# docker-compose.yml 添加 labels
services:
  frontend:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.frontend.entrypoints=websecure"
      - "traefik.http.routers.frontend.tls.certresolver=myresolver"
```

### 性能优化

#### 后端优化

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '1'
          memory: 512M
```

#### 前端优化

已内置：
- Gzip压缩
- 静态资源1年缓存
- HTTP/2支持（需HTTPS）

### 高可用部署

#### 多实例部署

```yaml
services:
  backend:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        max_attempts: 3
```

#### 负载均衡

使用 Docker Swarm 或 Kubernetes。

---

## 监控与日志

### 日志管理

#### 查看日志

```bash
# 所有服务日志
docker-compose logs

# 特定服务日志
docker-compose logs backend
docker-compose logs frontend

# 实时跟踪
docker-compose logs -f --tail=100
```

#### 日志持久化

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 健康检查

```bash
# 查看容器健康状态
docker inspect --format='{{json .State.Health}}' polytheater-backend

# 手动健康检查
curl http://localhost:5001/health
```

### Prometheus监控（可选）

```yaml
# 添加到 docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
```

---

## 故障排查

### 常见问题

#### 1. 容器无法启动

```bash
# 查看详细错误
docker-compose logs backend

# 检查配置
docker-compose config

# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

#### 2. API连接失败

```bash
# 检查后端是否运行
docker-compose ps

# 检查网络
docker network ls
docker network inspect polytheater_polytheater-network

# 测试连接
docker exec polytheater-frontend ping backend
```

#### 3. 前端无法访问后端

检查 nginx 配置中的 proxy_pass 地址：
```nginx
location /api {
    proxy_pass http://backend:5001;  # 使用服务名
}
```

#### 4. 文件上传失败

```bash
# 检查目录权限
ls -la backend/uploads

# 修复权限
chmod 755 backend/uploads
```

### 完全重置

```bash
# 停止并删除所有容器、网络、卷
docker-compose down -v

# 删除所有镜像
docker-compose down --rmi all

# 重新构建并启动
docker-compose up -d --build
```

---

## 备份与恢复

### 备份

```bash
# 备份上传文件
tar -czf polytheater-uploads-$(date +%Y%m%d).tar.gz backend/uploads/

# 备份环境配置
cp backend/.env polytheater-env-$(date +%Y%m%d).bak
```

### 恢复

```bash
# 恢复上传文件
tar -xzf polytheater-uploads-20240101.tar.gz

# 恢复环境配置
cp polytheater-env-20240101.bak backend/.env
```

---

## 更新与升级

### 更新应用

```bash
# 拉取最新代码
git pull origin main

# 重新构建并启动
docker-compose up -d --build

# 查看日志确认
docker-compose logs -f
```

### 版本回滚

```bash
# 切换到指定版本
git checkout <commit-hash>

# 重新部署
docker-compose up -d --build
```

---

## 附录

### Docker常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose stop

# 重启服务
docker-compose restart

# 查看状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 进入容器
docker-compose exec backend bash

# 清理未使用资源
docker system prune -a
```

### 安全建议

1. **不要在生产环境使用 `FLASK_DEBUG=true`**
2. **定期更新依赖版本**
3. **使用 secrets 管理敏感信息**：

```yaml
services:
  backend:
    secrets:
      - llm_api_key

secrets:
  llm_api_key:
    external: true
```

4. **限制容器权限**：

```yaml
services:
  backend:
    security_opt:
      - no-new-privileges:true
    read_only: true
```

---

## 支持

遇到问题？查看：

- [项目文档](./README.md)
- [API文档](./api.md)
- [问题反馈](../../issues)
