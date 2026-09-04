# Deployment Guide: WeatherGPT

WeatherGPT can be deployed via Docker Compose, Kubernetes, or native cloud services.

---

## 1. Local Native Development

### Backend
```powershell
# 1. Enter backend directory
cd backend

# 2. Run backend with uvicorn
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at `http://127.0.0.1:8000/docs`.

### Frontend
```powershell
# 1. Enter frontend directory
cd frontend

# 2. Start Vite development server
npm run dev
```
Dashboard will be available at `http://localhost:5173`.

---

## 2. Docker Compose Deployment

```bash
# Build and launch all containers
docker compose up --build -d

# Check running services
docker compose ps

# View logs
docker compose logs -f backend
```

Services started:
- `weathergpt_backend` on `http://localhost:8000`
- `weathergpt_frontend` on `http://localhost:80`
- `weathergpt_postgres` (PostGIS enabled) on port `5432`
- `weathergpt_redis` on port `6379`

---

## 3. Kubernetes Deployment

```bash
kubectl apply -f infra/kubernetes/configmap.yaml
kubectl apply -f infra/kubernetes/deployment.yaml
kubectl apply -f infra/kubernetes/service.yaml
```
