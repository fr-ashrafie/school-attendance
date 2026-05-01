# Face Recognition Attendance System

A production-ready school attendance system using face recognition, real-time updates, and comprehensive reporting.

## Tech Stack

- **Frontend**: React 18, Redux Toolkit, Material-UI, Socket.IO-client, Chart.js
- **Backend**: Django 4.2, Django REST Framework, Django Channels, Celery, Redis
- **Database**: PostgreSQL 15 with pgvector extension
- **Face Recognition**: Python face_recognition (dlib)
- **File Storage**: AWS S3 / MinIO
- **Auth**: JWT (Simple JWT)
- **Deployment**: Docker, Docker Compose

## Project Structure

```
school-attendance/
├── backend/                 # Django backend
│   ├── config/             # Django settings and configuration
│   ├── apps/               # Django applications
│   │   ├── accounts/       # User authentication and management
│   │   ├── students/       # Student management
│   │   ├── attendance/     # Attendance tracking
│   │   ├── reports/        # Report generation
│   │   └── notifications/  # Notification system
│   ├── scripts/            # Database setup scripts
│   ├── manage.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React frontend
│   ├── public/
│   ├── src/
│   │   ├── app/           # Redux store
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   └── utils/         # Utility functions
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd school-attendance
```

2. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start all services**
```bash
docker-compose up -d
```

4. **Run database migrations**
```bash
docker-compose exec backend python manage.py migrate
```

5. **Create superuser**
```bash
docker-compose exec backend python manage.py createsuperuser
```

6. **Enable pgvector extension**
```bash
docker-compose exec db psql -U postgres -d school_attendance -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

7. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Django Admin: http://localhost:8000/admin

## Environment Variables

See `.env.example` for all required environment variables.

### Required Variables

```bash
# Django
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=school_attendance
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# AWS S3 (or MinIO)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=us-east-1
AWS_S3_CUSTOM_DOMAIN=

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password
EMAIL_USE_TLS=True

# Face Recognition
FACE_RECOGNITION_TOLERANCE=0.6
FACE_DETECTION_MODEL=cnn
```

## API Documentation

### Authentication

#### Login
```bash
POST /api/auth/login/
Content-Type: application/json

{
  "email": "admin@school.com",
  "password": "password"
}
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Refresh Token
```bash
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Attendance

#### Capture Face Attendance
```bash
POST /api/attendance/capture/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

Response:
```json
{
  "success": true,
  "student": {
    "id": 1,
    "student_id": "STU001",
    "first_name": "John",
    "last_name": "Doe",
    "grade": "10A"
  },
  "attendance": {
    "id": 1,
    "status": "present",
    "timestamp": "2024-01-15T08:30:00Z",
    "marked_by": "face"
  },
  "confidence": 0.95
}
```

#### Get Today's Attendance Stats
```bash
GET /api/attendance/today/
Authorization: Bearer <access_token>
```

Response:
```json
{
  "date": "2024-01-15",
  "present": 245,
  "absent": 12,
  "late": 8,
  "total": 265
}
```

#### Get Student Attendance History
```bash
GET /api/attendance/student/{id}/?month=1&year=2024
Authorization: Bearer <access_token>
```

#### Manual Attendance Marking
```bash
POST /api/attendance/manual/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "student_id": 1,
  "status": "present",
  "date": "2024-01-15"
}
```

### Students

#### List/Search Students
```bash
GET /api/students/?search=john&grade=10A
Authorization: Bearer <access_token>
```

#### Get Student Profile
```bash
GET /api/students/{id}/
Authorization: Bearer <access_token>
```

### Reports

#### Generate Monthly Report
```bash
POST /api/reports/generate/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "month": 1,
  "year": 2024,
  "grade": "10A"
}
```

#### List Reports
```bash
GET /api/reports/
Authorization: Bearer <access_token>
```

### Notifications

#### Get Notifications
```bash
GET /api/notifications/
Authorization: Bearer <access_token>
```

#### Mark Notification as Read
```bash
PATCH /api/notifications/{id}/read/
Authorization: Bearer <access_token>
```

## WebSocket Connection

Connect to the WebSocket endpoint for real-time updates:

```javascript
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`ws://localhost:8000/ws/attendance/?token=${token}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'new_attendance') {
    // Update dashboard stats
    console.log('New attendance:', data.student);
  }
  
  if (data.type === 'notification') {
    // Show notification
    console.log('New notification:', data.notification);
  }
};
```

## Features

### 1. Real-time Attendance Tracking
- Capture student faces via webcam
- Instant face matching using pgvector cosine similarity
- Real-time updates via WebSocket
- Low confidence matches show top 3 candidates

### 2. Dashboard
- Today's attendance statistics (present/absent/late/total)
- 7-day attendance trend chart
- Live-updating recent activity feed
- Real-time status badges

### 3. Student Management
- Search by name or ID (debounced)
- Student profiles with photo and details
- Monthly attendance history
- Manual attendance correction
- Face re-registration

### 4. Reports
- PDF and Excel report generation
- Monthly reports per grade
- Automated generation on the 1st of each month
- S3 storage with download links

### 5. Notifications
- Daily absence notifications to parents
- In-app notifications with unread badge
- Email notifications
- Real-time delivery via WebSocket

### 6. Manual Attendance
- Override face recognition results
- Teacher-initiated attendance marking
- Audit trail with recorded_by_user

## Architecture Notes

### Database Schema

The system uses PostgreSQL with pgvector for efficient face encoding storage and similarity search.

**Key Tables:**
- `users`: Authentication and authorization
- `students`: Student information and photos
- `face_encodings`: Vector embeddings for face recognition
- `attendance_records`: Daily attendance logs
- `monthly_reports`: Generated report metadata
- `notifications`: User notifications

**Indexes:**
- IVFFlat index on `encoding_vector` for fast similarity search
- Composite index on `(student_id, date)` for attendance queries

### Face Recognition Pipeline

1. **Registration**: When a student photo is uploaded, multiple face encodings are computed and stored
2. **Capture**: Webcam image is sent to backend
3. **Detection**: Faces are located in the image
4. **Encoding**: Face embedding is computed
5. **Matching**: Cosine similarity search against stored encodings
6. **Recording**: Attendance record is created if match confidence > threshold

### Caching Strategy

- Dashboard stats cached in Redis with 60s TTL
- Cache invalidated on new attendance records
- Student search results cached for 5 minutes

### Scalability

- Connection pooling with PgBouncer
- Read replicas configurable via Django DATABASES setting
- Rate limiting on capture endpoint (10 requests/minute)
- Celery workers for async tasks
- Horizontal scaling supported via Docker Compose

## Celery Tasks

### Scheduled Tasks

1. **check_daily_absences** (10:00 AM daily)
   - Marks missing attendance records as absent
   - Creates notifications for absent students
   - Sends emails to parents

2. **generate_monthly_report** (1st of each month)
   - Generates PDF/Excel reports for all grades
   - Uploads to S3
   - Creates report records

3. **register_face_encodings** (On photo upload)
   - Computes face encodings for new photos
   - Stores multiple encodings per student

## Development

### Running Backend Locally

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Running Frontend Locally

```bash
cd frontend
npm install
npm start
```

### Running Tests

```bash
# Backend tests
docker-compose exec backend python manage.py test

# Frontend tests
docker-compose exec frontend npm test
```

## Production Deployment

### Docker Compose Production

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes

Manifests available in `k8s/` directory.

### Monitoring

- Prometheus metrics endpoint at `/metrics`
- Health check endpoint at `/health/`
- Logging configured for structured JSON output

## Security Considerations

- JWT tokens with short expiration
- HTTPS required in production
- CORS properly configured
- Rate limiting on sensitive endpoints
- Input validation and sanitization
- SQL injection prevention via ORM
- XSS protection via Django templates

## Troubleshooting

### Common Issues

1. **pgvector extension not found**
   ```bash
   docker-compose exec db psql -U postgres -c "CREATE EXTENSION vector;"
   ```

2. **Face recognition not working**
   - Ensure dlib dependencies are installed
   - Check FACE_RECOGNITION_TOLERANCE setting
   - Verify photos are clear and well-lit

3. **WebSocket connection failed**
   - Check token validity
   - Verify Daphne is running
   - Check CORS settings

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For issues and questions, please open an issue on GitHub.
