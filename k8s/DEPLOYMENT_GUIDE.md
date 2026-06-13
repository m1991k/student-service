# Kubernetes Deployment Guide

This guide demonstrates how to deploy the Student Service API and MongoDB to Kubernetes with:

- **Rolling updates** for seamless deployments
- **Self-healing** with liveness and readiness probes
- **External accessibility** via LoadBalancer service
- **Horizontal Pod Autoscaler (HPA)** for dynamic scaling
- **MongoDB cluster-internal access** only
- **Automatic recovery** from pod failures

## Requirements

- Kubernetes cluster (v1.20+)
- `kubectl` configured to access your cluster
- Optional: Metrics Server for HPA (usually pre-installed on managed clusters)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Kubernetes Cluster                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │       Service API Tier (Externally Exposed)      │  │
│  │   Type: LoadBalancer (External IP/Port 80)       │  │
│  └──────────────────────────────────────────────────┘  │
│           ↓                                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Deployment: student-app                         │  │
│  │  - Replicas: 4 pods                              │  │
│  │  - Strategy: Rolling Updates                     │  │
│  │  - Resource Limits: 256Mi mem, 500m cpu          │  │
│  └──────────────────────────────────────────────────┘  │
│           ↓                                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  HPA: student-app-hpa                            │  │
│  │  - Min: 2 replicas | Max: 10 replicas            │  │
│  │  - CPU: 70% threshold                            │  │
│  │  - Memory: 80% threshold                         │  │
│  └──────────────────────────────────────────────────┘  │
│           ↓                                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │   Database Tier (Cluster-Internal Only)          │  │
│  │   Type: ClusterIP (No External Access)           │  │
│  └──────────────────────────────────────────────────┘  │
│           ↓                                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  StatefulSet: mongodb                            │  │
│  │  - Replicas: 1 pod (currently)                   │  │
│  │  - Persistent Storage: PVC (5Gi)                 │  │
│  │  - Automatic recovery on pod deletion            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Deployment Steps

### 1. Create the Namespace

```bash
kubectl apply -f k8s/student-app-deployment.yaml
```

This creates:

- `student-app` namespace
- ConfigMap with application configuration
- Secret with MongoDB URI and credentials
- Deployment with 4 replicas, rolling update strategy, and probes
- LoadBalancer Service for external access
- HPA for automatic scaling
- PodDisruptionBudget for high availability

### 2. Deploy MongoDB

```bash
kubectl apply -f k8s/mongodb-deployment.yaml
```

This creates:

- PersistentVolumeClaim for data persistence
- StatefulSet for MongoDB with 1 replica
- Secret for MongoDB password
- ClusterIP Service (headless) for cluster-internal access only

### 3. Setup NGINX Ingress Controller (Optional - For Ingress Exposure)

If you want to expose the service via Ingress instead of LoadBalancer:

```bash
# Add NGINX Helm repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install NGINX Ingress Controller
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

### 4. Deploy Ingress Resource

```bash
kubectl apply -f k8s/ingress.yaml
```

This creates:

- IngressClass for NGINX
- Ingress resource that routes traffic to student-app service
- Updates the Service to use ClusterIP (not LoadBalancer)

**Configure DNS:**
Edit `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows):

```
<INGRESS-IP> student-api.example.com
```

Get the Ingress IP:

```bash
kubectl get ingress student-app-ingress -n student-app
```

### 5. Verify Deployment

```bash
# Check if resources are created
kubectl get all -n student-app

# Check pod status
kubectl get pods -n student-app
kubectl get pods -n student-app -w  # Watch for changes

# Check services
kubectl get svc -n student-app

# Check Ingress
kubectl get ingress -n student-app

# Check HPA status
kubectl get hpa -n student-app
```

## Features Demonstrated

### 1. Rolling Updates

The Deployment uses a rolling update strategy:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1 # Allows 1 extra pod during update
    maxUnavailable: 0 # No pods are unavailable during update
```

**Update the app image:**

```bash
kubectl set image deployment/student-app \
  student-app=m1991karm/student-service:v2 \
  -n student-app --record
```

**Monitor the rollout:**

```bash
kubectl rollout status deployment/student-app -n student-app
```

**Rollback if needed:**

```bash
kubectl rollout undo deployment/student-app -n student-app
```

### 2. Self-Healing with Probes

**Liveness Probe:** Restarts container if app is unresponsive

```yaml
livenessProbe:
  httpGet:
    path: /docs
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
```

**Readiness Probe:** Removes pod from load balancer if not ready

```yaml
readinessProbe:
  httpGet:
    path: /api/v1/students/
    port: 8000
  initialDelaySeconds: 15
  periodSeconds: 5
  failureThreshold: 2
```

**Test self-healing:**

```bash
# SSH into a pod and kill the process
kubectl exec -it <pod-name> -n student-app -- /bin/sh
kill 1

# Kubernetes will automatically restart it
kubectl get pods -n student-app -w
```

### 3. External Accessibility

The Service is exposed via LoadBalancer:

```yaml
apiVersion: v1
kind: Service
type: LoadBalancer
ports:
  - port: 80
    targetPort: 8000
```

**Get external IP:**

```bash
kubectl get svc student-app-service -n student-app
# For local cluster (minikube/docker-desktop):
# kubectl port-forward svc/student-app-service 8000:8000 -n student-app
```

**Access the API:**

```bash
# Get students
curl http://<EXTERNAL-IP>/api/v1/students/

# Access OpenAPI docs
open http://<EXTERNAL-IP>/docs
```

### 4. Horizontal Pod Autoscaler (HPA)

The HPA automatically scales based on CPU and memory:

```yaml
minReplicas: 2
maxReplicas: 10
metrics:
  - CPU: 70% utilization
  - Memory: 80% utilization
```

**Check HPA status:**

```bash
kubectl get hpa -n student-app
kubectl describe hpa student-app-hpa -n student-app
```

**Generate load to trigger scaling:**

```bash
# Install Apache Bench (ab) or use wrk
ab -n 10000 -c 100 http://<EXTERNAL-IP>/api/v1/students/

# Watch pods scale up
kubectl get pods -n student-app -w
```

**Monitor autoscaling:**

```bash
kubectl get hpa student-app-hpa -n student-app --watch
```

### 5. Ingress-Based External Access

Alternative to LoadBalancer, expose the API via NGINX Ingress Controller:

**Install NGINX Ingress Controller (if not already installed):**

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

**Deploy Ingress resource:**

```bash
kubectl apply -f k8s/ingress.yaml
```

**Check Ingress status:**

```bash
kubectl get ingress -n student-app
kubectl describe ingress student-app-ingress -n student-app
```

**Configure DNS (for production):**
Edit `/etc/hosts` or your DNS provider:

```
<INGRESS-IP> student-api.example.com
```

**Access via Ingress:**

```bash
# Get Ingress IP
INGRESS_IP=$(kubectl get ingress student-app-ingress -n student-app \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Access the API
curl http://$INGRESS_IP/api/v1/students/
curl http://$INGRESS_IP/docs
```

**Benefits of Ingress over LoadBalancer:**

- Single entry point for multiple services
- Path-based routing (`/api/*`, `/docs/*`, etc.)
- Optional TLS/HTTPS support
- Better resource utilization
- Built-in rate limiting and authentication options

### 6. MongoDB Cluster-Internal Access

MongoDB is only accessible within the cluster:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mongodb
spec:
  clusterIP: None # Headless service, cluster-internal only
  selector:
    app: mongodb
  ports:
    - port: 27017
```

**Verify MongoDB is not externally accessible:**

```bash
# From your machine
telnet <CLUSTER-IP> 27017
# Will timeout - no external access

# But accessible from within cluster
kubectl exec -it <pod-name> -n student-app -- \
  mongosh --host mongodb --username admin
```

### 7. Automatic Recovery (Pod Deletion)

MongoDB uses StatefulSet with persistent storage for recovery:

**Test recovery by deleting a pod:**

```bash
# Delete the MongoDB pod
kubectl delete pod mongodb-0 -n student-app

# StatefulSet recreates it automatically
kubectl get pods -n student-app -w

# Data persists in PVC
kubectl get pvc -n student-app
```

**Verify data persistence:**

```bash
# Check if data directory is recreated
kubectl exec -it mongodb-0 -n student-app -- \
  ls -la /data/db/
```

## Configuration Management

### Updating Configuration

**Update via ConfigMap:**

```bash
kubectl set env deployment/student-app \
  DEBUG=true \
  -n student-app --record
```

**Update Secret:**

```bash
kubectl create secret generic student-app-secret \
  --from-literal=MONGO_URI='mongodb://...' \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Monitoring and Troubleshooting

### Check Deployment Status

```bash
# Get deployment info
kubectl get deployment student-app -n student-app

# Describe deployment
kubectl describe deployment student-app -n student-app

# View recent events
kubectl get events -n student-app --sort-by='.lastTimestamp'
```

### View Logs

```bash
# View pod logs
kubectl logs <pod-name> -n student-app

# Follow logs in real-time
kubectl logs -f <pod-name> -n student-app

# View logs from all pods
kubectl logs -l app=student-app -n student-app -f
```

### Debug Pod Issues

```bash
# SSH into a pod
kubectl exec -it <pod-name> -n student-app -- /bin/sh

# Check resource usage
kubectl top pods -n student-app
kubectl top nodes

# Describe pod for detailed info
kubectl describe pod <pod-name> -n student-app
```

## Cleanup

```bash
# Delete everything in the namespace
kubectl delete namespace student-app

# Or delete individual resources
kubectl delete deployment student-app -n student-app
kubectl delete statefulset mongodb -n student-app
kubectl delete pvc mongodb-pvc -n student-app
```

## Production Considerations

1. **Use persistent storage backend** (AWS EBS, GCP PD, etc.)
2. **Enable RBAC** for security
3. **Use Network Policies** to restrict traffic
4. **Implement resource quotas** at namespace level
5. **Use private container registries** instead of Docker Hub
6. **Enable audit logging** for compliance
7. **Configure pod security policies** for security
8. **Use sealed secrets** for sensitive data
9. **Implement backup strategies** for MongoDB data
10. **Monitor with Prometheus/Grafana** for observability

## Troubleshooting Common Issues

### Pods not starting

```bash
kubectl describe pod <pod-name> -n student-app
kubectl logs <pod-name> -n student-app
```

### Service not accessible

```bash
kubectl get svc -n student-app
kubectl port-forward svc/student-app-service 8000:8000 -n student-app
```

### HPA not scaling

```bash
kubectl get hpa -n student-app
kubectl describe hpa student-app-hpa -n student-app
# Ensure metrics-server is running
kubectl get deployment metrics-server -n kube-system
```

### MongoDB connection issues

```bash
# Check if MongoDB pod is running
kubectl get pods -n student-app -l app=mongodb

# Check service DNS
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  nslookup mongodb.student-app.svc.cluster.local
```

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Deployment Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [HPA Documentation](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
