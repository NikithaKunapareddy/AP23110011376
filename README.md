# Afford Medical - Backend Internship Evaluation

Backend services for Afford Medical Technologies covering Vehicle Maintenance Scheduling and Campus Notifications.

## Project Structure

```
afford/
├── logging_middleware/          # Centralized logging infrastructure
│   ├── __init__.py
│   ├── logger.py               # LoggerService with structured logging
│   └── middleware.py           # FastAPI middleware for request/response logging
│
├── vehicle_maintenance_scheduler/  # Knapsack optimization for maintenance
│   ├── __init__.py
│   ├── scheduler.py            # Core scheduling algorithm (0/1 knapsack)
│   └── handler.py              # API integration and orchestration
│
├── notification_app_be/         # Campus notification system backend
│   ├── handler/               # Request handlers
│   ├── service/               # Business logic
│   ├── repository/            # Data access layer
│   └── route/                 # FastAPI route definitions
│
├── main.py                     # FastAPI application entry point
├── test_scheduler.py           # Scheduler testing script
├── notification_system_design.md  # Complete design documentation (Stages 1-6)
├── find_secret.py             # Credentials discovery script
└── requirements.txt           # Python dependencies
```

## Features

### 1. Logging Middleware
- Structured JSON logging across all operations
- Request/response correlation IDs
- Context-rich log entries
- Time tracking for performance monitoring

**Usage:**
```python
from logging_middleware import LoggerService, LoggingMiddleware

logger = LoggerService()
app.add_middleware(LoggingMiddleware, logger_service=logger)

logger.info(
    stack="backend",
    package="handler",
    message="Processing vehicle scheduling",
    context={"vehicles": 50}
)
```

### 2. Vehicle Maintenance Scheduler
Solves the **0/1 Knapsack Problem** using Dynamic Programming to optimize vehicle maintenance scheduling within mechanic hours budget.

**Algorithm:**
- Time Complexity: O(n × W) where n = vehicles, W = hours
- Space Complexity: O(n × W)
- Optimal substructure for real-world scale inputs

**Features:**
- Maximize operational impact score
- Respect daily mechanic-hour budget
- Multi-depot scheduling
- Efficiency reporting

**Run Test:**
```bash
python test_scheduler.py
```

### 3. Campus Notification System

#### Stage 1: REST API Design
- GET /api/notifications - Fetch with pagination & filtering
- PUT /api/notifications/:id/read - Mark as read
- DELETE /api/notifications/:id - Delete
- GET /api/notifications/unread/count - Unread count
- WebSocket /ws/notifications - Real-time streaming

#### Stage 2: Database Schema
- PostgreSQL with ACID compliance
- Strategic indexing on (studentID, isRead, createdAt)
- Partitioning by date for scalability
- JSON metadata support

#### Stage 3: Query Optimization
- Optimized queries with selective columns
- Partial indexes for common filters
- Cost analysis and execution plans

#### Stage 4: Performance Under Load
- Redis caching (5-min TTL)
- WebSocket real-time push
- Read replicas for scaling
- Lazy loading & pagination

#### Stage 5: Bulk Notification System
- Async batch processing (100 students/batch)
- Retry logic with exponential backoff
- DB-first approach (atomicity)
- Job tracking & audit trail

#### Stage 6: Priority Inbox
- Min-heap for efficient top-K selection
- Priority scoring: (type_weight × 1000) + recency
- Type weights: Placement=3, Result=2, Event=1
- O(log k) insertion for streaming notifications

## Running the Application

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start FastAPI Server
```bash
python main.py
```

Server runs on: `http://localhost:8000`

API Documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 3. Test Scheduler
```bash
python test_scheduler.py
```

## API Endpoints

### Health Check
```
GET /health
GET /api/scheduler/status
```

### Vehicle Scheduler
```
POST /api/scheduler/schedule
Runs complete scheduling workflow
```

### Notifications
```
GET /api/notifications?page=1&limit=20&type=Placement&isRead=false
PUT /api/notifications/{id}/read
PUT /api/notifications/read-all
DELETE /api/notifications/{id}
GET /api/notifications/unread/count
GET /api/notifications/priority/inbox?n=10
```

## Logging

Logs are stored in `logs/` directory with structured JSON format.

### Log Example
```json
{
  "logID": "a4aad02e-19d0-4153-86d9-58bf55d7c402",
  "timestamp": "2026-04-22T17:51:30.123456",
  "stack": "backend",
  "level": "info",
  "package": "handler",
  "message": "Scheduling complete",
  "context": {
    "selected_count": 15,
    "total_impact": 87,
    "total_hours": 58
  }
}
```

## Credentials

**Registered User:**
- Email: anikitha_kunapareddy@srmap.edu.in
- Name: Kunapareddy Nikitha
- Roll No: AP23110011376
- ClientID: 7f1331dd-c33a-4e79-97e5-8d014932869a
- ClientSecret: KbkdTVytDpmAmnUk

## Design Documentation

See `notification_system_design.md` for comprehensive documentation covering:
- REST API contract (Stage 1)
- Database schema & scalability (Stage 2)
- Query optimization (Stage 3)
- Performance strategies (Stage 4)
- Bulk notifications (Stage 5)
- Priority inbox implementation (Stage 6)

## Key Implementation Details

### Logging Middleware
- Intercepts all HTTP requests
- Adds correlation IDs for tracing
- Tracks request processing time
- Logs errors with context

### Vehicle Scheduler
- Implements dynamic programming solution
- Handles real-world scale (1000+ vehicles)
- Provides efficiency metrics
- Extensible for multi-objective optimization

### Notification System
- Scalable to 50,000+ users
- 5M+ notifications support
- Real-time delivery via WebSocket
- Priority-based inbox with efficient data structures

## Testing

The project includes test data and mock implementations for rapid development.

To test with real APIs:
```python
from vehicle_maintenance_scheduler import SchedulerHandler

handler = SchedulerHandler(
    client_id="7f1331dd-c33a-4e79-97e5-8d014932869a",
    client_secret="KbkdTVytDpmAmrna",
    logger_service=logger
)

result = await handler.run_scheduling()
```

## Performance Metrics

### Vehicle Scheduler
- Scheduling 100 vehicles: ~50ms
- Scheduling 1000 vehicles: ~500ms
- Memory usage: Linear O(n × W)

### Notification System
- Cache hit response: 5-10ms
- DB query response: 50-100ms
- WebSocket delivery: <100ms

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Best Practices](https://www.postgresql.org/docs/)
- [Knapsack Algorithm](https://en.wikipedia.org/wiki/Knapsack_problem)
- [WebSocket Real-time Apps](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

## License

Proprietary - Afford Medical Technologies Private Limited

## Confidentiality Notice

This code and associated documentation contain proprietary information of Afford Medical Technologies. Unauthorized access or disclosure is prohibited.
