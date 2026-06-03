# API Reference

The Explainer Video Factory exposes an asynchronous FastAPI service for triggering and monitoring render jobs.

## Endpoints

### `GET /api/v1/health`
Check the health status of the API server.
- **Response**: `{"status": "ok", "version": "0.1.0", "environment": "development"}`

### `POST /api/v1/render`
Submit a new render job to the background queue.
- **Request Body**:
  ```json
  {
    "topic": "Quantum Entanglement",
    "difficulty": "intermediate"
  }
  ```
- **Response**: `{"job_id": "uuid...", "status": "pending", "topic": "...", "message": "..."}`

### `GET /api/v1/render/{job_id}`
Retrieve the progress and status of a render job.
- **Response**: Contains status, progress details, and output URLs if completed.
