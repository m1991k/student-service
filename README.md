# Student Service API

A FastAPI-based microservice for managing student records with MongoDB as the database.

## Links

- **GitHub Repository:** https://github.com/m1991k/student-service.git
- **Docker Hub Image:** m1991karm/student-service:v1
- **OpenAPI Documentation:** http://127.0.0.1:8000/docs

## Features

- RESTful API for student management (Create, Read, Update, Delete)
- MongoDB integration with async Motor driver
- Pydantic models for data validation
- Comprehensive logging for debugging
- Docker containerized deployment
- Interactive API documentation with Swagger UI

## Prerequisites

- Python 3.12+
- Docker & Docker Compose (for containerized deployment)
- MongoDB 7.0+

## Installation

### Local Development

1. **Clone the repository:**

   ```bash
   git clone https://github.com/m1991k/student-service.git
   cd student-service
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv mkvenv
   source mkvenv/bin/activate  # On Windows: mkvenv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB credentials
   ```

5. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://127.0.0.1:8000`

## Docker Deployment

### Prerequisites

- Ensure MongoDB is running:
  ```bash
  docker run -d --name mongodb -p 27017:27017 \
    -v mongodb_data:/data/db \
    -e MONGO_INITDB_ROOT_USERNAME=admin \
    -e MONGO_INITDB_ROOT_PASSWORD=Admin@123 \
    -e MONGO_INITDB_DATABASE=school \
    mongo:7
  ```

### Build the Image

```bash
docker build -t student-service:latest .
```

### Run the Container

**PowerShell:**

```powershell
docker run -d `
  --name student-app `
  -p 8000:8000 `
  --link mongodb:mongo `
  -e "MONGO_URI=mongodb://admin:Admin%40123@mongodb:27017/?authSource=admin" `
  -e "MONGO_DB=school" `
  student-service:latest
```

**Command Prompt (cmd):**

```cmd
docker run -d ^
  --name student-app ^
  -p 8000:8000 ^
  --link mongodb:mongo ^
  -e MONGO_URI=mongodb://admin:Admin%%40123@mongodb:27017/?authSource=admin ^
  -e MONGO_DB=school ^
  student-service:latest
```

### Run with Docker Hub Image

```bash
docker run -d \
  --name student-app \
  -p 8000:8000 \
  --link mongodb:mongo \
  -e MONGO_URI=mongodb://admin:Admin%40123@mongodb:27017/?authSource=admin \
  -e MONGO_DB=school \
  m1991karm/student-service:latest
```

### Verify Container is Running

```bash
docker ps
docker logs student-app
```

## API Endpoints

### Student Management

- **GET** `/api/v1/students/` - Get all students
- **POST** `/api/v1/students/` - Create a new student
- **GET** `/api/v1/students/{student_id}` - Get student by ID
- **PUT** `/api/v1/students/{student_id}` - Update student
- **DELETE** `/api/v1/students/{student_id}` - Delete student

### Example Requests

**Get all students:**

```bash
curl http://127.0.0.1:8000/api/v1/students/
```

**Create a student:**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/students/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "age": 20,
    "email": "john@example.com"
  }'
```

## API Documentation

Interactive API documentation is available at:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

## Project Structure

```
student-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── student_routes.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── db/
│   │   ├── __init__.py
│   │   └── mongodb.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── student.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── student_repository.py
│   └── services/
│       └── student_service.py
├── Dockerfile
├── requirements.txt
├── .env
└── README.md
```

## Environment Variables

- `MONGO_URI` - MongoDB connection string
- `MONGO_DB` - MongoDB database name
- `APP_NAME` - Application name
- `DEBUG` - Debug mode (true/false)

## Configuration

Edit `.env` file with your settings:

```env
MONGO_URI=mongodb://admin:Admin@123@localhost:27017/?authSource=admin
MONGO_DB=school
APP_NAME=Student Service
DEBUG=false
```

## Logging

The application includes comprehensive logging for debugging:

- Request logging in route handlers
- Database operation logging in repository
- Error logging with full stack traces
- MongoDB connection logging

View logs:

```bash
# Local development
docker logs student-app

# Or check the application console
```

## License

MIT License

## Support

For issues and questions, visit: https://github.com/m1991k/student-service/issues
