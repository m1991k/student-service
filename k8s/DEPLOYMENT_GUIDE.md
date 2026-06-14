# Kubernetes Deployment Guide

This guide demonstrates how to deploy the Student Service API and MongoDB to Kubernetes with:

- **Rolling updates** for seamless deployments
- **Self-healing** with liveness and readiness probes
- **External accessibility** via Ingress
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
│  │   Type:  Ingress                                 │  │
│  └──────────────────────────────────────────────────┘  │
│           ↓                                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Deployment: student-app                         │  │
│  │  - Replicas: 4 pods (configurable via HPA)       │  │
│  │  - Strategy: Rolling Updates                     │  │
│  │  - Resource Limits: 256Mi mem, 500m cpu          │  │
│  └──────────────────────────────────────────────────┘  │
│           ↓                                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  HPA: student-app-hpa                            │  │
│  │  - Min: 2 replicas | Max: 10 replicas            │  │
│  │  - CPU: 70% threshold                            │  │
│  │  - Memory: 80% utilization                       │  │
│  └──────────────────────────────────────────────────┘  │
│           ↓                                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Namespace: student-app                          │  │
│  │  └─ Isolates all resources in this namespace     │  │
│  └──────────────────────────────────────────────────┘  │
│           ↓                                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │   Database Tier (Cluster-Internal Only)          │  │
│  │   Type: ClusterIP Service (Headless)             │  │
│  └──────────────────────────────────────────────────┘  │
│           ↓                                              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  StatefulSet: mongodb                            │  │
│  │  - Replicas: 1 pod                               │  │
│  │  - Storage: PVC (5Gi) ↔ PV (5Gi)                 │  │
│  │  - Persistent data at /data/db                   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## YAML Files Summary

| File                          | Purpose                                                                | Type                                             | Namespace     |
| ----------------------------- | ---------------------------------------------------------------------- | ------------------------------------------------ | ------------- |
| `student-app-namespace.yaml`  | Creates namespace and labels                                           | Namespace                                        | N/A           |
| `persistent-volume.yaml`      | Defines PV for MongoDB storage                                         | PersistentVolume                                 | cluster-wide  |
| `mongodb-deployment.yaml`     | MongoDB StatefulSet + PVC + Secret + Service                           | StatefulSet, PVC, Secret, Service                | `student-app` |
| `student-app-deployment.yaml` | App Deployment + ConfigMap + Secret + LoadBalancer Service + HPA + PDB | Deployment, ConfigMap, Secret, Service, HPA, PDB | `student-app` |
| `ingress.yaml`                | NGINX IngressClass + Ingress + ClusterIP Service                       | IngressClass, Ingress, Service                   | `student-app` |

## Deployment Steps

### 1. Create the Namespace

```bash
kubectl apply -f k8s/student-app-namespace.yaml
```

This creates:

- `student-app` namespace with appropriate labels

**Verify namespace creation:**

```bash
kubectl get namespace student-app
```

### 2. Create Persistent Volume (Optional - For Local Development)

```bash
kubectl apply -f k8s/persistent-volume.yaml
```

This creates:

- `mongodb-pv` PersistentVolume with 5Gi capacity
- Storage class: `standard`
- Reclaim policy: `Retain` (data persists after PVC deletion)
- hostPath backend (for local clusters like minikube/docker-desktop)

**For Production:** Replace hostPath with cloud storage (AWS EBS, GCP PD, Azure Disk, etc.)

**Verify PV creation:**

```bash
kubectl get pv
kubectl describe pv mongodb-pv
```

### 3. Deploy MongoDB

```bash
kubectl apply -f k8s/mongodb-deployment.yaml
```

This creates:

- PersistentVolumeClaim (5Gi) that binds to the PersistentVolume
- StatefulSet for MongoDB with 1 replica
- Secret with MongoDB root password
- ClusterIP Service (headless) for cluster-internal access only

**Verify MongoDB deployment:**

```bash
kubectl get pods -n student-app -l app=mongodb
kubectl get pvc -n student-app
kubectl get statefulset -n student-app
```

### 4. Deploy Student Application

```bash
kubectl apply -f k8s/student-app-deployment.yaml
```

This creates:

- ConfigMap with application configuration
- Secret with MongoDB URI and credentials
- Deployment with 4 replicas, rolling update strategy, and probes
- ClusterIP Service to expose API using ingress
- HPA (Horizontal Pod Autoscaler) for automatic scaling
- PodDisruptionBudget for high availability

**Verify application deployment:**

```bash
kubectl get deployment student-app -n student-app
kubectl get pods -n student-app -l app=student-app
kubectl get svc -n student-app
```

### 5. Setup NGINX Ingress Controller (Optional - For Ingress-Based Exposure)

If you want to expose the service via Ingress instead of LoadBalancer (recommended for production):

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

**Verify NGINX Ingress Controller installation:**

```bash
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```

### 6. Deploy Ingress Resource

```bash
kubectl apply -f k8s/ingress.yaml
```

This creates:

- IngressClass for NGINX controller configuration
- Ingress resource that routes traffic from `student-api.example.com` to student-app service
- Single entry point for all API requests
- Annotations for SSL redirect, rate limiting, and rewrite rules
- ClusterIP Service (updated from LoadBalancer)

**Verify Ingress deployment:**

```bash
kubectl get ingress -n student-app
kubectl describe ingress student-app-ingress -n student-app
```

**Configure DNS:**
Edit `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows):

```
<INGRESS-IP> student-api.example.com
```

Get the Ingress IP:

```bash
kubectl get ingress student-app-ingress -n student-app
# Look for external IP or hostname in the INGRESS column
```

### 7. Verify Full Deployment

```bash
# Check all resources in the namespace
kubectl get all -n student-app

# Check persistent volumes and claims
kubectl get pv,pvc -n student-app

# Check ingress
kubectl get ingress -n student-app

# Watch pod status
kubectl get pods -n student-app -w
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

The application can be exposed via:

**Option A: LoadBalancer Service** (configured in `student-app-deployment.yaml`)

```yaml
type: LoadBalancer
ports:
  - port: 80
    targetPort: 8000
```

Get external IP:

```bash
kubectl get svc student-app-service -n student-app
# For local cluster (minikube/docker-desktop):
kubectl port-forward svc/student-app-service 8000:8000 -n student-app
```

**Option B: Ingress with NGINX** (configured in `ingress.yaml` - recommended for production)

```bash
kubectl get ingress student-app-ingress -n student-app
# Access via: http://student-api.example.com (after DNS setup)
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

### 5. Ingress-Based External Access (Production Recommended)

Alternative to LoadBalancer, expose the API via NGINX Ingress Controller for better resource utilization and advanced routing:

**Benefits of Ingress over LoadBalancer:**

- Single entry point for multiple services
- Path-based and host-based routing
- Built-in rate limiting and SSL/TLS support
- Better for multi-service architectures
- Reduced cloud infrastructure costs

**Complete Ingress Setup (All Steps):**

```bash
# 1. Create namespace first
kubectl apply -f k8s/student-app-namespace.yaml

# 2. Create persistent volume
kubectl apply -f k8s/persistent-volume.yaml

# 3. Deploy MongoDB
kubectl apply -f k8s/mongodb-deployment.yaml

# 4. Deploy Student App (with LoadBalancer)
kubectl apply -f k8s/student-app-deployment.yaml

# 5. Install NGINX Ingress Controller via Helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer

# 6. Deploy Ingress resource (routes to student-app service)
kubectl apply -f k8s/ingress.yaml
```

**Verify Ingress setup:**

```bash
# Check Ingress Controller
kubectl get pods -n ingress-nginx

# Check Ingress resource
kubectl get ingress -n student-app
kubectl describe ingress student-app-ingress -n student-app

# Get Ingress IP/Hostname
kubectl get ingress student-app-ingress -n student-app -o jsonpath='{.status.loadBalancer.ingress[0]}'
```

**Configure DNS (for production):**
Edit `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows):

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

# Or via hostname (after DNS setup)
curl http://student-api.example.com/api/v1/students/
```

**Ingress Features (from `ingress.yaml`):**

- **SSL Redirect**: Forces HTTPS connections
- **Rate Limiting**: 100 requests per second
- **Cert Manager Integration**: Automatic HTTPS with Let's Encrypt
- **Rewrite Target**: Normalizes request paths

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

### 8. Persistent Volume and Storage Management

**Monitor storage usage:**

```bash
# Check PersistentVolume status
kubectl get pv
kubectl describe pv mongodb-pv

# Check PersistentVolumeClaim binding
kubectl get pvc -n student-app
kubectl describe pvc mongodb-pvc -n student-app
```

**Resize PersistentVolume (for production scenarios):**

```bash
# Edit the PVC to request more storage
kubectl edit pvc mongodb-pvc -n student-app
# Update: spec.resources.requests.storage to desired size
```

**Storage Backends:**

- **Local Development**: `hostPath` (current implementation in `persistent-volume.yaml`)
- **Production Recommendations**:
  - AWS: EBS volumes
  - GCP: Persistent Disks
  - Azure: Azure Disks
  - On-premises: NFS or block storage

**Switch to different storage class:**

```bash
# Check available storage classes
kubectl get storageclass

# Update mongodb-deployment.yaml to use different storageClassName
```

**Backup MongoDB data:**

```bash
# Create backup
kubectl exec -it mongodb-0 -n student-app -- \
  mongodump --uri="mongodb://admin:Admin@123@localhost:27017" --out=/tmp/backup

# Extract from pod
kubectl cp student-app/mongodb-0:/tmp/backup ./backup-local
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

**Complete Cleanup (remove everything):**

```bash
# 1. Remove Ingress and Helm release
kubectl delete ingress student-app-ingress -n student-app
helm uninstall nginx-ingress -n ingress-nginx

# 2. Delete the entire student-app namespace (removes all resources within)
kubectl delete namespace student-app

# 3. Delete Persistent Volume (if using local storage)
kubectl delete pv mongodb-pv

# 4. Remove ingress-nginx namespace (if no longer needed)
kubectl delete namespace ingress-nginx
```

**Selective Cleanup (remove specific resources):**

```bash
# Delete only the application deployment
kubectl delete deployment student-app -n student-app

# Delete only MongoDB
kubectl delete statefulset mongodb -n student-app

# Delete PersistentVolumeClaim (WARNING: data will be lost!)
kubectl delete pvc mongodb-pvc -n student-app

# Delete Ingress only
kubectl delete ingress student-app-ingress -n student-app

# Delete the namespace
kubectl delete namespace student-app
```

**Warning:** Deleting a PersistentVolumeClaim with `Retain` policy will preserve the data, but will need manual cleanup of the PersistentVolume:

```bash
kubectl delete pv mongodb-pv
# If using hostPath, manually remove: /mnt/data/mongodb
```

## Production Considerations

1. **Persistent Storage Backend**
   - Replace `hostPath` with cloud storage (AWS EBS, GCP PD, Azure Disk)
   - Configure appropriate `storageClassName` in `persistent-volume.yaml`
   - Set `persistentVolumeReclaimPolicy` to `Delete` for automatic cleanup

2. **Namespace Isolation**
   - Use the `student-app` namespace from `student-app-namespace.yaml`
   - Apply resource quotas at namespace level
   - Use Network Policies to restrict traffic

3. **Ingress Setup**
   - Deploy via `ingress.yaml` with NGINX Ingress Controller
   - Configure SSL/TLS certificates (Let's Encrypt integration included)
   - Enable rate limiting (100 req/sec configured)

4. **Data Persistence & Backup**
   - Regularly backup MongoDB data
   - Test backup restoration procedures
   - Monitor PVC usage and resize as needed
   - Implement automated backup solutions

5. **Security**
   - Use RBAC for access control
   - Store secrets in secure vaults (not in YAML)
   - Use sealed-secrets or external secret management
   - Enable pod security policies

6. **Monitoring**
   - Install Prometheus and Grafana for metrics
   - Setup AlertManager for critical alerts
   - Enable audit logging for compliance
   - Monitor PV/PVC usage and performance

7. **High Availability**
   - Scale MongoDB to 3+ replicas for production
   - Update HPA limits based on expected load
   - Configure PodDisruptionBudgets (included)

8. **Resource Management**
   - Set CPU and memory requests/limits (configured in YAML files)
   - Implement resource quotas at namespace level
   - Monitor and optimize resource consumption

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
