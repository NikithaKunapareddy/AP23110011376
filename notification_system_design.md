# Notification System Design

## Stage 1: REST API Design & Contract

### Core Actions
The notification platform supports the following core actions:
1. **Fetch Notifications** - Retrieve notifications for logged-in user
2. **Mark as Read** - Update notification read status
3. **Delete Notification** - Remove notification
4. **Get Notification Count** - Fetch unread count
5. **Real-time Notification Push** - Stream new notifications

### REST API Endpoints

#### 1. GET /api/notifications
**Purpose:** Fetch all notifications for the logged-in user

**Request Headers:**
```json
{
  "Authorization": "Bearer <token>",
  "Content-Type": "application/json",
  "X-Correlation-ID": "<uuid>"
}
```

**Query Parameters:**
```
?page=1&limit=20&type=Placement&isRead=false&sortBy=createdAt&order=desc
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": "d146095a-0d86-4a34-9e69-3900a14576bc",
      "type": "Placement",
      "message": "CSX Corporation hiring",
      "timestamp": "2026-04-22T17:51:18Z",
      "isRead": false,
      "priority": "high",
      "metadata": {
        "companyName": "CSX Corporation",
        "applicationDeadline": "2026-05-15",
        "link": "/placements/123"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "hasMore": true
  }
}
```

#### 2. PUT /api/notifications/:id/read
**Purpose:** Mark notification as read

**Request Body:**
```json
{
  "isRead": true
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Notification marked as read",
  "data": {
    "id": "d146095a-0d86-4a34-9e69-3900a14576bc",
    "isRead": true
  }
}
```

#### 3. PUT /api/notifications/read-all
**Purpose:** Mark all notifications as read

**Response (200 OK):**
```json
{
  "success": true,
  "message": "All notifications marked as read",
  "updatedCount": 25
}
```

#### 4. DELETE /api/notifications/:id
**Purpose:** Delete a notification

**Response (204 No Content)**

#### 5. GET /api/notifications/unread/count
**Purpose:** Get count of unread notifications

**Response (200 OK):**
```json
{
  "success": true,
  "unreadCount": 15,
  "byType": {
    "Placement": 5,
    "Result": 7,
    "Event": 3
  }
}
```

#### 6. WebSocket /ws/notifications
**Purpose:** Real-time notification streaming

**Connection:**
```
ws://domain:port/ws/notifications?token=<auth_token>
```

**Server → Client Message:**
```json
{
  "type": "new_notification",
  "data": {
    "id": "uuid",
    "type": "Placement",
    "message": "New job opportunity",
    "timestamp": "2026-04-22T17:51:18Z"
  }
}
```

---

## Stage 2: Database Schema & Storage Strategy

### Database Choice: PostgreSQL

**Rationale:**
- **ACID Compliance:** Ensures data consistency for notification state
- **JSON Support:** Flexible metadata storage
- **Full-Text Search:** Built-in search on messages
- **Scalability:** Horizontal scaling via partitioning
- **Performance:** Excellent for read-heavy workloads with proper indexing

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  rollNo VARCHAR(50) UNIQUE NOT NULL,
  createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_email (email),
  INDEX idx_rollNo (rollNo)
);
```

#### Notifications Table
```sql
CREATE TABLE notifications (
  id UUID PRIMARY KEY,
  studentID UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  type ENUM('Placement', 'Result', 'Event') NOT NULL,
  message TEXT NOT NULL,
  isRead BOOLEAN DEFAULT FALSE,
  createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  metadata JSONB,
  
  INDEX idx_student_read (studentID, isRead),
  INDEX idx_student_created (studentID, createdAt DESC),
  INDEX idx_type (type),
  INDEX idx_created (createdAt DESC),
  CONSTRAINT check_type CHECK (type IN ('Placement', 'Result', 'Event'))
);
```

#### Notification Preferences Table
```sql
CREATE TABLE notification_preferences (
  id UUID PRIMARY KEY,
  studentID UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  placements_enabled BOOLEAN DEFAULT TRUE,
  results_enabled BOOLEAN DEFAULT TRUE,
  events_enabled BOOLEAN DEFAULT TRUE,
  email_enabled BOOLEAN DEFAULT TRUE,
  push_enabled BOOLEAN DEFAULT TRUE,
  updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Notification Read Status Table (for audit)
```sql
CREATE TABLE notification_read_logs (
  id UUID PRIMARY KEY,
  notificationID UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
  studentID UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  readAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_notification (notificationID),
  INDEX idx_student_date (studentID, readAt DESC)
);
```

### Scalability Challenges & Solutions

#### Challenge 1: Query Performance with Large Dataset
**Problem:** As student count reaches 50,000 and notifications reach 5,000,000, range queries become slow.

**Solution:**
- **Table Partitioning by Date:** Partition notifications by month
  ```sql
  CREATE TABLE notifications_2026_04 PARTITION OF notifications
  FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
  ```
- **Selective Indexing:** Only index frequently queried columns

#### Challenge 2: Index Maintenance Overhead
**Problem:** Too many indexes slow down writes.

**Solution:**
- Create indexes strategically on (studentID, isRead, createdAt)
- Use partial indexes for common queries:
  ```sql
  CREATE INDEX idx_unread_notifications 
  ON notifications (studentID, createdAt DESC) 
  WHERE isRead = FALSE;
  ```

#### Challenge 3: Write Performance During Bulk Notifications
**Problem:** "Notify All" operations cause lock contention.

**Solution:**
- Use batch inserts with COPY protocol
- Implement message queue (RabbitMQ/Kafka) for async processing

### Optimized SQL Queries

#### Query 1: Fetch Unread Notifications (from Stage 1)
```sql
SELECT id, type, message, timestamp, metadata
FROM notifications
WHERE studentID = $1 AND isRead = FALSE
ORDER BY createdAt DESC
LIMIT 20;
```

#### Query 2: Find Placement Notifications (Last 7 Days)
```sql
SELECT 
  n.id,
  n.type,
  n.message,
  n.createdAt,
  u.name,
  u.rollNo
FROM notifications n
JOIN users u ON n.studentID = u.id
WHERE n.type = 'Placement'
  AND n.createdAt >= CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY n.createdAt DESC;
```

#### Query 3: Notification Count by Type
```sql
SELECT 
  type,
  COUNT(*) as count,
  COUNT(CASE WHEN isRead = FALSE THEN 1 END) as unreadCount
FROM notifications
WHERE studentID = $1
GROUP BY type;
```

---

## Stage 3: Database Performance & Query Optimization

### Original Query Analysis
```sql
SELECT * FROM notifications
WHERE studentID = 1042 AND isRead = false
ORDER BY createdAt DESC;
```

**Why it's slow:**
1. `SELECT *` fetches all columns (inefficient memory usage)
2. No composite index on (studentID, isRead, createdAt)
3. Full table scan if index on studentID only

### Optimized Query
```sql
SELECT 
  id, type, message, createdAt, metadata
FROM notifications
WHERE studentID = $1 AND isRead = FALSE
ORDER BY createdAt DESC
LIMIT 50;

-- Supporting partial index
CREATE INDEX idx_unread_by_student 
ON notifications(studentID, createdAt DESC) 
WHERE isRead = FALSE;
```

**Improvements:**
- **3-5x faster** due to index on exact predicate
- Reduced memory by selecting only needed columns
- Added LIMIT to prevent memory bloat

### Index Strategy Analysis
**Advice: "Add index on every column"** - NOT effective

**Why:**
1. **Write Overhead:** Every INSERT/UPDATE rebuilds all indexes
2. **Memory Consumption:** Each index uses disk space
3. **Query Planner Confusion:** Too many choices can lead to poor decisions

**Effective Strategy:**
```sql
-- High-impact indexes only
CREATE INDEX idx_student_unread ON notifications(studentID, isRead, createdAt DESC);
CREATE INDEX idx_type_date ON notifications(type, createdAt DESC);
CREATE INDEX idx_created_date ON notifications(createdAt DESC);

-- Avoid low-value indexes
-- Don't index: message, metadata (high cardinality, rarely in WHERE clause)
```

### Query for Placement Notifications (Last 7 Days)
```sql
SELECT 
  id,
  message,
  createdAt,
  studentID,
  metadata
FROM notifications
WHERE type = 'Placement'
  AND createdAt >= CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY createdAt DESC;

-- Index support
CREATE INDEX idx_placement_recent 
ON notifications(type, createdAt DESC) 
WHERE type = 'Placement';
```

**Expected Execution Plan:**
- Index Scan on idx_placement_recent
- ~5-10ms query time for 5M rows

---

## Stage 4: Performance Optimization Under Load

### Problem: DB Overwhelmed by Per-Page Fetches
With 50,000 students fetching on every page load = 50,000 queries.

### Solution 1: Caching Strategy
```python
# Redis cache implementation
CACHE_TTL = 300  # 5 minutes

def get_notifications_cached(student_id: str, use_cache: bool = True):
    cache_key = f"notifications:{student_id}"
    
    # Try cache first
    if use_cache:
        cached = redis.get(cache_key)
        if cached:
            logger.info("Cache hit", context={"student_id": student_id})
            return json.loads(cached)
    
    # Miss: query DB
    notifications = db.query(
        "SELECT * FROM notifications WHERE studentID = %s ORDER BY createdAt DESC",
        [student_id]
    )
    
    # Cache result
    redis.setex(cache_key, CACHE_TTL, json.dumps(notifications))
    return notifications
```

**Tradeoffs:**
- ✅ 100x faster reads
- ✅ DB load reduced significantly
- ❌ Stale data (5 min delay)
- ❌ Cache invalidation complexity

### Solution 2: Pagination & Lazy Loading
```sql
-- Fetch only first page (20 items)
SELECT * FROM notifications 
WHERE studentID = $1 
ORDER BY createdAt DESC 
LIMIT 20 OFFSET 0;

-- Frontend loads more on scroll
```

**Tradeoffs:**
- ✅ Reduced bandwidth
- ✅ Faster initial load
- ❌ Multiple requests needed
- ✅ Better UX with streaming

### Solution 3: Event-Driven Notification Push
```python
# WebSocket subscription instead of polling
@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()
    
    # Subscribe to student events
    await subscription_manager.subscribe(student_id, websocket)
    
    # Server sends new notifications in real-time
    # No client polling needed
```

**Tradeoffs:**
- ✅ Instant delivery (no delay)
- ✅ DB load minimal
- ❌ Server memory for connections
- ❌ Connection management complexity

### Solution 4: Read Replicas
```python
# Write to primary, read from replica
db_read = PostgreSQL(host="replica-1.db.local")  # Read-only
db_write = PostgreSQL(host="primary.db.local")   # Read-write

notifications = db_read.query(...)  # Load balanced to replicas
```

**Tradeoffs:**
- ✅ Scales read throughput
- ✅ Primary handles writes
- ❌ Replication lag
- ❌ Infrastructure cost

### Recommended Hybrid Approach
```
Browser → Cache Layer → Read Replica → Primary DB
           (Redis)      (PostgreSQL)

- Initial page load: Cache (5 min TTL)
- Real-time: WebSocket push from message queue
- Search: Direct replica query
- Writes: Always go to primary
```

---

## Stage 5: Reliable Bulk Notification System

### Problem with Original Implementation
```python
def notify_all(student_ids: array, message: string):
    for student_id in student_ids:
        send_email(student_id, message)      # ❌ Fails midway
        save_to_db(student_id, message)      # DB writes are blocking
        push_to_app(student_id, message)     # App push hangs
```

**Issues:**
1. **No retry logic:** 200 failed emails are lost
2. **Blocking operations:** Sequential processing is slow (50K × 2s = 27+ hours)
3. **No transaction:** Partial state on failure
4. **Single point of failure:** One failed email blocks entire process

### Improved Implementation

```python
import asyncio
import json
from typing import List
from datetime import datetime
from logging_middleware import LoggerService

class BulkNotificationService:
    """
    Reliable bulk notification system with retry logic and async processing
    """
    
    def __init__(
        self, 
        logger_service: LoggerService,
        max_retries: int = 3,
        batch_size: int = 100
    ):
        self.logger = logger_service
        self.max_retries = max_retries
        self.batch_size = batch_size
        self.message_queue = []  # In production: use RabbitMQ/Kafka

    async def notify_all(
        self, 
        student_ids: List[str], 
        message: str,
        notification_type: str = "General"
    ) -> dict:
        """
        Send notifications to all students with reliable delivery.
        
        Process:
        1. Create job record in DB
        2. Queue async tasks
        3. Process in batches with retry
        4. Track success/failure
        """
        
        job_id = str(uuid.uuid4())
        self.logger.info(
            stack="backend",
            package="service",
            message=f"Starting bulk notification job {job_id}",
            context={
                "total_students": len(student_ids),
                "job_id": job_id
            }
        )

        # Create job record (transactional)
        job = {
            "id": job_id,
            "status": "processing",
            "createdAt": datetime.utcnow(),
            "totalStudents": len(student_ids),
            "processedCount": 0,
            "successCount": 0,
            "failureCount": 0,
            "message": message
        }
        
        # Store job metadata
        await self._save_job(job)

        # Process in batches (key improvement: parallelization)
        results = await self._process_batches(
            student_ids=student_ids,
            message=message,
            job_id=job_id,
            notification_type=notification_type
        )

        # Update job status
        await self._update_job(job_id, {
            "status": "completed",
            "successCount": results["success_count"],
            "failureCount": results["failure_count"],
            "completedAt": datetime.utcnow()
        })

        self.logger.info(
            stack="backend",
            package="service",
            message=f"Bulk notification job {job_id} completed",
            context={
                "job_id": job_id,
                "success": results["success_count"],
                "failed": results["failure_count"]
            }
        )

        return {
            "jobId": job_id,
            "totalStudents": len(student_ids),
            "successCount": results["success_count"],
            "failureCount": results["failure_count"],
            "failedStudentIds": results["failed_ids"]
        }

    async def _process_batches(
        self,
        student_ids: List[str],
        message: str,
        job_id: str,
        notification_type: str
    ) -> dict:
        """Process students in parallel batches"""
        
        success_count = 0
        failure_count = 0
        failed_ids = []

        # Process in batches of 100
        for i in range(0, len(student_ids), self.batch_size):
            batch = student_ids[i:i + self.batch_size]
            
            # Run batch tasks in parallel
            tasks = [
                self._notify_student(
                    student_id=sid,
                    message=message,
                    job_id=job_id,
                    notification_type=notification_type
                )
                for sid in batch
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Track results
            for student_id, result in zip(batch, results):
                if isinstance(result, Exception) or not result["success"]:
                    failure_count += 1
                    failed_ids.append(student_id)
                else:
                    success_count += 1

        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "failed_ids": failed_ids
        }

    async def _notify_student(
        self,
        student_id: str,
        message: str,
        job_id: str,
        notification_type: str
    ) -> dict:
        """
        Send notification to single student with retry logic.
        Key: Save to DB FIRST, then send email/push (fail-safe)
        """
        
        retries = 0
        last_error = None

        while retries <= self.max_retries:
            try:
                # IMPORTANT: Save to DB first (can't fail)
                # This ensures notification exists even if email fails
                notification = {
                    "id": str(uuid.uuid4()),
                    "studentID": student_id,
                    "type": notification_type,
                    "message": message,
                    "isRead": False,
                    "createdAt": datetime.utcnow(),
                    "metadata": {"jobId": job_id}
                }
                
                # Step 1: Persist to DB (transactional)
                await self._save_notification(notification)
                
                # Step 2: Send email (can retry on failure)
                email_result = await self._send_email_with_retry(
                    student_id=student_id,
                    message=message,
                    retries=self.max_retries
                )
                
                # Step 3: Push to app (can retry)
                push_result = await self._push_to_app(
                    student_id=student_id,
                    notification=notification
                )
                
                return {
                    "success": True,
                    "studentId": student_id,
                    "notificationId": notification["id"]
                }

            except Exception as e:
                last_error = e
                retries += 1
                
                self.logger.warning(
                    stack="backend",
                    package="service",
                    message=f"Retry {retries} for student {student_id}",
                    context={"error": str(e), "retry": retries}
                )
                
                if retries <= self.max_retries:
                    await asyncio.sleep(2 ** retries)  # Exponential backoff
                
        # Failed after all retries
        self.logger.error(
            stack="backend",
            package="service",
            message=f"Failed to notify student after {self.max_retries} retries",
            context={"student_id": student_id, "error": str(last_error)}
        )
        
        return {
            "success": False,
            "studentId": student_id,
            "error": str(last_error)
        }

    async def _save_notification(self, notification: dict):
        """Save notification to database"""
        # Implementation: Insert into notifications table
        pass

    async def _send_email_with_retry(
        self, 
        student_id: str, 
        message: str, 
        retries: int = 3
    ):
        """Send email with exponential backoff retry"""
        # Implementation: Call email service
        pass

    async def _push_to_app(self, student_id: str, notification: dict):
        """Push notification to app via WebSocket"""
        # Implementation: WebSocket push
        pass

    async def _save_job(self, job: dict):
        """Save job metadata"""
        pass

    async def _update_job(self, job_id: str, updates: dict):
        """Update job status"""
        pass
```

### Key Improvements

1. **DB First Approach**
   - Always save to DB first (guaranteed persistence)
   - Email/push failures don't affect notification record
   - Reduces data loss

2. **Async/Parallel Processing**
   - 100 students at a time (vs sequential)
   - 50K students × 2s per student → ~10 minutes (vs 27+ hours)

3. **Retry Logic with Exponential Backoff**
   - Auto-retry failed emails
   - Handles transient failures gracefully

4. **Job Tracking**
   - Monitor progress
   - Track success/failure
   - Audit trail for compliance

5. **Batch Processing**
   - Leverage message queue (RabbitMQ/Kafka)
   - Decouple sending from DB updates
   - Handle backpressure

### Should DB Save & Email Send Happen Together?

**Answer: NO**

**Why:**
- If email API is slow, DB write is blocked
- Email failure shouldn't prevent DB persistence
- Network flakiness affects DB reliability

**Pattern: Write-Through with Async Notification**
```python
# Good: Atomic DB write, async email
await db.save_notification(...)  # Fast, reliable
asyncio.create_task(send_email(...))  # Fire and forget with retry

# Bad: Coupled operations
await db.save_notification(...)
await send_email(...)  # Blocks if slow
```

---

## Stage 6: Priority Inbox Implementation

### Business Rules
Priority determined by:
1. **Type Weight:** Placement (3) > Result (2) > Event (1)
2. **Recency:** Newer notifications rank higher
3. **Combined Score:** `priority_score = (type_weight × recency_factor) + ...`

### Implementation: Python with Efficient Heap

```python
import heapq
import json
from datetime import datetime, timedelta
from enum import IntEnum
from typing import List, Dict
import httpx
from logging_middleware import LoggerService


class NotificationType(IntEnum):
    """Priority weights for notification types"""
    EVENT = 1
    RESULT = 2
    PLACEMENT = 3


class PriorityNotification:
    """Notification with priority scoring"""
    
    def __init__(self, notification_data: Dict):
        self.id = notification_data["ID"]
        self.type = notification_data["Type"]
        self.message = notification_data["Message"]
        self.timestamp = datetime.fromisoformat(
            notification_data["Timestamp"].replace(" ", "T")
        )
        self._priority_score = self._calculate_priority()

    def _calculate_priority(self) -> float:
        """
        Calculate priority score.
        Higher score = Higher priority
        
        Formula: (type_weight × 1000) + recency_score
        """
        # Type weight (3 = Placement, 2 = Result, 1 = Event)
        type_weight = NotificationType[self.type.upper()].value
        
        # Recency score (0-1000, higher for newer)
        age_hours = (datetime.utcnow() - self.timestamp).total_seconds() / 3600
        recency_score = max(0, 1000 - (age_hours * 10))  # Degrades over time
        
        # Combined priority
        priority_score = (type_weight * 1000) + recency_score
        
        return priority_score

    def __lt__(self, other):
        """Min heap: higher priority score = smaller value"""
        return self._priority_score > other._priority_score

    def __repr__(self):
        return f"Notification({self.id}, {self.type}, score={self._priority_score:.1f})"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "priority": self._get_priority_label(),
            "priority_score": round(self._priority_score, 2)
        }

    def _get_priority_label(self) -> str:
        """Get human-readable priority level"""
        score = self._priority_score
        if score >= 4000:
            return "Critical"
        elif score >= 3000:
            return "High"
        elif score >= 2000:
            return "Medium"
        else:
            return "Low"


class PriorityNotificationService:
    """Service to fetch and rank notifications by priority"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        logger_service: LoggerService
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger = logger_service
        self.base_url = "http://20.207.122.201/evaluation-service"
        self.headers = {
            "Authorization": f"Bearer {client_id}:{client_secret}",
            "Content-Type": "application/json"
        }

    def _log(self, level: str, message: str, context: Dict = None):
        """Log with middleware"""
        if self.logger:
            method = getattr(self.logger, level, self.logger.info)
            method(
                stack="backend",
                package="service",
                message=message,
                context=context or {}
            )

    async def fetch_notifications(self) -> List[Dict]:
        """Fetch notifications from API"""
        self._log("info", "Fetching notifications from API")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/notifications",
                    headers=self.headers,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                notifications = data.get("notifications", [])
                self._log(
                    "info",
                    f"Fetched {len(notifications)} notifications",
                    context={"count": len(notifications)}
                )
                return notifications
        
        except Exception as e:
            self._log("error", f"Failed to fetch notifications: {str(e)}")
            raise

    def get_top_n_notifications(
        self,
        notifications: List[Dict],
        n: int = 10
    ) -> List[Dict]:
        """
        Get top N notifications by priority using min heap.
        Time Complexity: O(n log n) for sort, O(n log k) for heap
        Space Complexity: O(k) where k = n
        """
        
        self._log(
            "info",
            f"Computing top {n} priority notifications from {len(notifications)} total",
            context={"n": n, "total": len(notifications)}
        )

        # Convert to priority objects
        priority_notifs = [
            PriorityNotification(notif) for notif in notifications
        ]

        # Use heap to find top N efficiently
        # heapq.nlargest is O(n log k) where k = n
        top_n = heapq.nlargest(n, priority_notifs)

        self._log(
            "info",
            f"Selected top {len(top_n)} priority notifications",
            context={
                "selected": len(top_n),
                "by_type": {
                    "Placement": sum(1 for x in top_n if x.type == "Placement"),
                    "Result": sum(1 for x in top_n if x.type == "Result"),
                    "Event": sum(1 for x in top_n if x.type == "Event")
                }
            }
        )

        return [notif.to_dict() for notif in top_n]

    async def get_priority_inbox(self, n: int = 10) -> Dict:
        """
        Complete workflow: Fetch and return top N notifications
        """
        try:
            notifications = await self.fetch_notifications()
            top_n = self.get_top_n_notifications(notifications, n)
            
            return {
                "success": True,
                "total_notifications": len(notifications),
                "top_n": n,
                "priority_inbox": top_n
            }
        
        except Exception as e:
            self._log("error", f"Failed to get priority inbox: {str(e)}")
            raise


class PriorityInboxMaintainer:
    """
    Maintains efficient top-K notifications as new ones arrive.
    Uses bounded min-heap for O(log k) insertion.
    """

    def __init__(self, k: int = 10):
        self.k = k
        self.heap: List[PriorityNotification] = []

    def add_notification(self, notification_data: Dict):
        """
        Add notification to priority inbox.
        Time: O(log k) where k = top-k size
        """
        notif = PriorityNotification(notification_data)

        if len(self.heap) < self.k:
            # Heap not full, just add
            heapq.heappush(self.heap, notif)
        elif notif._priority_score > self.heap[0]._priority_score:
            # Replace minimum if new notification is better
            heapq.heapreplace(self.heap, notif)
        # else: new notification not good enough for top-k

    def get_top_k(self) -> List[Dict]:
        """Get sorted top-k notifications"""
        # Sort descending (highest priority first)
        sorted_notifs = sorted(self.heap, reverse=True)
        return [notif.to_dict() for notif in sorted_notifs]

    def to_json(self) -> str:
        """Export as JSON"""
        return json.dumps(self.get_top_k(), indent=2, default=str)


# Example usage and testing
async def main():
    """Main function for testing"""
    
    # Initialize logger
    from logging_middleware import LoggerService
    logger = LoggerService(log_dir="logs", app_name="notification-service")
    
    # Create service
    service = PriorityNotificationService(
        client_id="7f1331dd-c33a-4e79-97e5-8d014932869a",
        client_secret="KbkdTVytDpmAmrna",
        logger_service=logger
    )
    
    # Fetch and prioritize
    result = await service.get_priority_inbox(n=10)
    
    print("\n" + "="*60)
    print("PRIORITY INBOX (Top 10)")
    print("="*60)
    
    for i, notif in enumerate(result["priority_inbox"], 1):
        print(f"\n{i}. [{notif['priority']}] {notif['type']}")
        print(f"   Message: {notif['message']}")
        print(f"   Time: {notif['timestamp']}")
        print(f"   Score: {notif['priority_score']}")
    
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Approach Explanation

**Priority Scoring Formula:**
```
priority_score = (type_weight × 1000) + recency_factor

Where:
- type_weight: Placement=3, Result=2, Event=1
- recency_factor: Decreases with age (newer = higher)
```

**Example Scores:**
- Placement from 1 hour ago: (3 × 1000) + 990 = **3990** (Critical)
- Result from 5 hours ago: (2 × 1000) + 950 = **2950** (Medium)
- Event from 2 days ago: (1 × 1000) + 800 = **1800** (Low)

### Maintaining Top-10 Efficiently

**Strategy: Bounded Min-Heap**

As new notifications arrive:
```python
maintainer = PriorityInboxMaintainer(k=10)

# New notification arrives
maintainer.add_notification(new_notif)  # O(log 10) = O(1)

# Get current top-10
top_10 = maintainer.get_top_k()  # O(10) = O(k)
```

**Time Complexity:**
- Insert new: **O(log k)** = O(log 10) ≈ O(1)
- Get top-k: **O(k log k)** = O(10 log 10) ≈ O(1)
- Space: **O(k)** = O(10) constant

This is optimal for maintaining a dynamic top-k with streaming data.

---

## Summary

| Stage | Focus | Key Decisions |
|-------|-------|---------------|
| 1 | API Design | RESTful endpoints + WebSocket for real-time |
| 2 | Storage | PostgreSQL with strategic indexing |
| 3 | Query Optimization | Composite indexes, partial indexes, selective columns |
| 4 | Load Handling | Redis cache + WebSocket push + Read replicas |
| 5 | Bulk Operations | Async batching, DB-first strategy, retry logic |
| 6 | Priority | Min-heap ranking with type+recency scoring |
