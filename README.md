# Student Service API

A FastAPI-based microservice for managing student records with MongoDB as the database.

## Links

- **GitHub Repository:** https://github.com/m1991k/student-service.git
- **Docker Hub Image:** m1991karm/student-service:v1
- **OpenAPI Documentation:** http://127.0.0.1:8000/docs

### Student API endpoints

- **GET** `/api/v1/health` - Get application health
- **GET** `/api/v1/students` - Get all students
- **POST** `/api/v1/students` - Create a new student
- **GET** `/api/v1/students/{student_id}` - Get student by ID
- **PUT** `/api/v1/students/{student_id}` - Update student
- **DELETE** `/api/v1/students/{student_id}` - Delete student

### Example Requests

**Get all students:**

```bash
curl http://127.0.0.1:8000/api/v1/students
```

**Create a student:**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/students \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "age": 20,
    "email": "john@example.com"
  }'
```

## Demo

1. Deploy namespace : below resource should be created

- namespace

2. Deploy Database : below resources should be created

- secret
- persistance volume and persistance volume claim
- statefulset
- service

3. Deploy API : below resources should be created

- secret and configmap
- deployment and replicaset
- service

4. Deploy ingress: below resources should be created

- ingress
- wait for some time for IP assignment

5. Access API via ingress
6. Self healing

- delete api pod and it should be recreated
- delete database pod and it should be recreated with same name

7. Persistence

- create some student records
- check those data is returned from API
- delete database pod and it should be recreated
- check same data is still returned from API

8. Deployment strategy : rolling update

- run "kubectl set image deployment/student-app student-app=m1991karm/student-service:v2 -n student-app" command to update the image
- check one by one pod is replaced with new pod having new image version

9. HPA

- deploy HPA resource
- run command "kubectl get hpa -n student-app" to check cpu and memory usage
- run "kubectl run -i --tty load-generator --rm --image=busybox:1.28 --restart=Never -- /bin/sh -c "while true; do wget -q -O- http://34.69.68.155/api/v1/students; done"" command to generate load to app
- check cpu and memory usage is increasing
- check new pods are created
