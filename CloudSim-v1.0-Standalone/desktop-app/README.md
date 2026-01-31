# CloudSim Desktop Application

A student-focused desktop application for learning cloud computing concepts locally.

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python main.py
```

## Project Structure

```
desktop-app/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── ui/                          # User interface components
│   ├── main_window.py          # Main application window
│   ├── sidebar.py              # Navigation sidebar
│   └── views/                  # Service-specific views
│       ├── compute_view.py     # Compute instances UI
│       ├── storage_view.py     # Storage buckets UI
│       ├── database_view.py    # Database tables UI
│       └── serverless_view.py  # Lambda functions UI
```

## Current Status

**Phase 1: UI Skeleton (Current)**
- ✅ Main window with sidebar navigation
- ✅ View switching between services
- ✅ Basic layout for Compute, Storage, Database, Serverless views
- ⏳ Backend integration (not yet implemented)

## Features (Planned)

- **Compute**: Create and manage Docker containers as instances
- **Storage**: S3-like bucket management with MinIO
- **Database**: DynamoDB-like NoSQL tables
- **Serverless**: Deploy and test Python Lambda functions

## Requirements

- Python 3.8 or higher
- PySide6 (Qt for Python)
- Docker Desktop (for backend features)

## Development

This is a skeleton UI version. Backend services and Docker integration will be added in future updates.

## For Students

This application is designed to help you understand cloud computing concepts through hands-on practice without cloud account costs or risks.
