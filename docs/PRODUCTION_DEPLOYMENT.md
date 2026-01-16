# Production Deployment Guide

This guide covers deploying Quantum AI PCB Builder to production environments.

## Pre-Deployment Checklist

### Security
- [ ] Configure specific CORS origins (remove wildcard `*`)
- [ ] Set up HTTPS/TLS certificates
- [ ] Implement user authentication (JWT recommended)
- [ ] Add API rate limiting
- [ ] Enable request/response validation
- [ ] Set up firewall rules
- [ ] Configure secure environment variables
- [ ] Enable audit logging

### Infrastructure
- [ ] Migrate to production-grade database (PostgreSQL)
- [ ] Set up Redis for caching
- [ ] Configure load balancer
- [ ] Set up CDN for frontend assets
- [ ] Implement backup strategy
- [ ] Configure monitoring and alerting
- [ ] Set up log aggregation
- [ ] Plan disaster recovery

### Performance
- [ ] Enable response compression
- [ ] Configure caching headers
- [ ] Optimize Docker images
- [ ] Set resource limits (CPU/Memory)
- [ ] Configure connection pooling
- [ ] Enable database query optimization

### Scalability
- [ ] Implement horizontal pod autoscaling
- [ ] Set up multiple worker instances
- [ ] Configure RabbitMQ clustering
- [ ] Enable database replication
- [ ] Set up container orchestration (Kubernetes)

## Environment Configuration

### Production Environment Variables

```bash
# Security
OPENAI_API_KEY=prod_key_here
SECRET_KEY=your_secure_secret_key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database (recommended: PostgreSQL)
DATABASE_URL=postgresql://user:pass@db-host:5432/pcb_builder
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis (for caching)
REDIS_URL=redis://redis-host:6379/0

# RabbitMQ (production cluster)
RABBITMQ_HOST=rabbitmq-cluster.internal
RABBITMQ_PORT=5672
RABBITMQ_USER=prod_user
RABBITMQ_PASS=secure_password
RABBITMQ_VHOST=/prod

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
WORKERS=4  # Number of uvicorn workers

# Monitoring
SENTRY_DSN=your_sentry_dsn
PROMETHEUS_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Docker Production Configuration

### docker-compose.prod.yml

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: pcb_builder
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  rabbitmq:
    image: rabbitmq:3-management
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS}
      RABBITMQ_DEFAULT_VHOST: ${RABBITMQ_VHOST}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    restart: always
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - RABBITMQ_HOST=rabbitmq
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: python -m app.worker
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - RABBITMQ_HOST=rabbitmq
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    restart: always
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '2'
          memory: 2G

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
      args:
        - REACT_APP_API_URL=${API_URL}
    restart: always
    deploy:
      replicas: 2

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - static_files:/usr/share/nginx/html
    depends_on:
      - backend
      - frontend
    restart: always

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
  static_files:
```

## Production Dockerfiles

### backend/Dockerfile.prod

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install production dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-prod.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run with multiple workers
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### frontend/Dockerfile.prod

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## Nginx Configuration

### nginx.conf

```nginx
upstream backend {
    least_conn;
    server backend:8000 max_fails=3 fail_timeout=30s;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000" always;

    # Frontend
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no rate limit)
    location /health {
        proxy_pass http://backend;
        access_log off;
    }
}
```

## Kubernetes Deployment

### k8s/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pcb-builder-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pcb-builder-backend
  template:
    metadata:
      labels:
        app: pcb-builder-backend
    spec:
      containers:
      - name: backend
        image: your-registry/pcb-builder-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: pcb-builder-secrets
              key: database-url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: pcb-builder-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: pcb-builder-backend
spec:
  selector:
    app: pcb-builder-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pcb-builder-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pcb-builder-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'pcb-builder-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'rabbitmq'
    static_configs:
      - targets: ['rabbitmq:15692']
```

### Grafana Dashboards

Import these dashboards:
- FastAPI metrics: Dashboard ID 12056
- RabbitMQ: Dashboard ID 10991
- PostgreSQL: Dashboard ID 9628
- Redis: Dashboard ID 11835

## Backup Strategy

### Database Backup

```bash
#!/bin/bash
# backup-db.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"

# Create backup
pg_dump $DATABASE_URL | gzip > $BACKUP_FILE

# Upload to S3
aws s3 cp $BACKUP_FILE s3://your-bucket/backups/

# Keep only last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

### Design Files Backup

```bash
#!/bin/bash
# backup-designs.sh

DESIGNS_DIR="/app/designs"
BACKUP_DIR="/backups/designs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create tarball
tar -czf $BACKUP_DIR/designs_$TIMESTAMP.tar.gz $DESIGNS_DIR

# Upload to S3
aws s3 cp $BACKUP_DIR/designs_$TIMESTAMP.tar.gz s3://your-bucket/designs/

# Keep only last 90 days
find $BACKUP_DIR -name "designs_*.tar.gz" -mtime +90 -delete
```

## Deployment Steps

1. **Prepare Environment**
   ```bash
   # Copy production config
   cp .env.prod .env
   
   # Generate secrets
   openssl rand -base64 32 > secret_key.txt
   ```

2. **Build Images**
   ```bash
   docker compose -f docker-compose.prod.yml build
   ```

3. **Database Migration**
   ```bash
   # Run migrations (when implemented)
   docker compose -f docker-compose.prod.yml run backend alembic upgrade head
   ```

4. **Deploy**
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

5. **Verify Deployment**
   ```bash
   # Check health
   curl https://yourdomain.com/health
   
   # Check API docs
   curl https://yourdomain.com/docs
   ```

## Maintenance

### Log Rotation

```bash
# /etc/logrotate.d/pcb-builder
/var/log/pcb-builder/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 appuser appuser
    sharedscripts
    postrotate
        docker-compose -f /app/docker-compose.prod.yml restart backend
    endscript
}
```

### Updates

```bash
# Zero-downtime deployment
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --no-deps --build backend
docker compose -f docker-compose.prod.yml up -d --no-deps --build worker
docker compose -f docker-compose.prod.yml up -d --no-deps --build frontend
```

## Troubleshooting

### High Memory Usage
- Check worker processes: `docker stats`
- Review RabbitMQ queue depth
- Check for memory leaks in logs

### Slow API Responses
- Check database query performance
- Review Redis cache hit ratio
- Check backend worker count

### Failed Deployments
- Review logs: `docker compose logs`
- Check health endpoints
- Verify environment variables

## Security Hardening

- Enable AppArmor/SELinux
- Use Docker secrets instead of env vars
- Implement network policies
- Regular security updates
- Vulnerability scanning
- Penetration testing

## Cost Optimization

- Use spot instances for workers
- Implement auto-scaling
- Optimize Docker image sizes
- Use CDN for static assets
- Enable response compression
- Implement caching strategy

---

For support, open an issue on GitHub or contact the team.
