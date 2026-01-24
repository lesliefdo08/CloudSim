# CloudSim Console - Local AWS Simulator

> **Educational cloud platform simulator for learning AWS concepts without costs or complexity**

![CloudSim v1.0](CloudSim%20Logo.png)

## Overview

CloudSim Console is a desktop application that simulates AWS cloud services locally, providing students and professionals with a safe, cost-free environment to learn cloud computing concepts. Built with PySide6, it features an authentic AWS Console-inspired interface with realistic resource management.

## Features

### Core Services
- **EC2 Instances** - Launch and manage virtual servers with realistic state management
- **S3 Storage** - Create buckets, upload/download files with versioning support
- **EBS Volumes** - Block storage volumes with attach/detach capabilities
- **RDS Databases** - Provision MySQL/PostgreSQL databases with connection management
- **Lambda Functions** - Deploy and test serverless functions with runtime support
- **IAM Simulation** - Role-based access control and permissions (educational mode)

### Monitoring & Management
- **Activity Log** - CloudTrail-style event tracking for all resource operations
- **Cost Dashboard** - Real-time cost estimation and billing insights
- **Resource Metrics** - CPU, memory, and storage usage monitoring
- **Regional Resources** - Multi-region support with latency simulation

## Download & Run

### For End Users (No Python Required)

1. **Download** the latest release: [CloudSim-v1.0-Windows.exe](https://github.com/lesliefdo08/CloudSim/releases/tag/v1.0)
2. **Extract** the ZIP file
3. **Run** `CloudSim.exe`
4. **Start Learning** - No installation, AWS account, or cloud costs needed!

### System Requirements
- Windows 10/11 (64-bit)
- 4 GB RAM minimum
- 500 MB disk space
- No internet connection required

## Screenshots

*CloudSim provides an AWS-like experience with familiar interfaces for EC2, S3, RDS, Lambda, and more.*

## For Developers

### Setup
```bash
# Clone repository
git clone https://github.com/lesliefdo08/CloudSim.git
cd CloudSim/desktop-app

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Build Executable
```bash
cd desktop-app
pyinstaller cloudsim.spec
# Output: dist/CloudSim/CloudSim.exe
```

## Architecture

```
CloudSim/
├── desktop-app/          # Desktop application source
│   ├── ui/               # User interface components
│   │   ├── views/        # Service views (EC2, S3, RDS, etc.)
│   │   ├── components/   # Reusable UI components
│   │   └── design_system.py  # Centralized styling
│   ├── services/         # Backend cloud service simulation
│   │   ├── compute_service.py
│   │   ├── storage_service.py
│   │   ├── database_service.py
│   │   └── serverless_service.py
│   ├── models/           # Data models
│   ├── utils/            # Utilities and helpers
│   └── data/             # Local data persistence
├── config/               # Configuration files
└── docs/                 # Additional documentation
```

## Technology Stack

- **Framework**: PySide6 (Qt for Python)
- **Language**: Python 3.10+
- **Storage**: Local JSON files
- **Build**: PyInstaller for Windows executables

## Educational Purpose

CloudSim is designed specifically for:
- Students learning cloud computing concepts
- Professionals preparing for AWS certifications
- Instructors teaching cloud infrastructure
- Anyone wanting hands-on AWS experience without costs

### What Makes It Different?
- ✅ No AWS account required
- ✅ No cloud costs - completely free
- ✅ Works offline
- ✅ Instant resource provisioning
- ✅ Safe experimentation environment
- ✅ Realistic AWS Console UI

## Version

**CloudSim v1.0** - Released January 2026

## Developer

**Developed by Leslie Fernando**

## License

Educational Use Only

---

## Contributing

This is an educational project. For issues, questions, or suggestions, please open an issue on GitHub.

## Roadmap

Future enhancements may include:
- Additional AWS services (SNS, SQS, CloudWatch)
- Docker container support
- Network simulation (VPC, Security Groups)
- CloudFormation-style templates
- Multi-user collaboration mode

---

© 2026 CloudSim - Your Local Cloud Learning Platform
