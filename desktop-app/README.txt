CloudSim Desktop - Local Cloud Learning Platform
Version 1.0.0

==============================================
GETTING STARTED
==============================================

1. Double-click "CloudSim.exe" to launch the application
2. The CloudSim console will open with a dashboard view
3. No installation, Python, or internet connection required!

==============================================
FEATURES
==============================================

☁️ DASHBOARD
   - Real-time overview of all cloud resources
   - Metrics for compute, storage, database, and serverless

🖥️ COMPUTE SERVICE (EC2-like)
   - Create virtual machine instances
   - Start, stop, and delete instances
   - Choose instance types and configurations

📦 STORAGE SERVICE (S3-like)
   - Create storage buckets
   - Upload and download files
   - Manage objects in buckets

🗄️ DATABASE SERVICE (RDS/DynamoDB-like)
   - Create relational (SQL) databases
   - Create NoSQL document databases
   - Insert, query, and manage data

⚡ SERVERLESS SERVICE (Lambda-like)
   - Write Python functions
   - Test with JSON events
   - See execution logs and output

==============================================
NAVIGATION
==============================================

- Use the TOP NAVIGATION BAR for quick service access
- Use the LEFT SIDEBAR for alternative navigation
- Click "Dashboard" to return to the overview
- Check the STATUS BAR at the bottom for system status

==============================================
LEARNING CLOUD CONCEPTS
==============================================

CloudSim teaches real AWS cloud concepts:

✓ EC2 (Elastic Compute Cloud) - Virtual servers
✓ S3 (Simple Storage Service) - Object storage
✓ RDS (Relational Database Service) - SQL databases
✓ DynamoDB - NoSQL databases
✓ Lambda - Serverless functions
✓ CloudWatch - Dashboard monitoring (metrics)
✓ Regions - Multi-region concepts (educational)

Everything runs LOCALLY on your computer - no cloud account needed!

==============================================
DATA STORAGE
==============================================

CloudSim stores all data in a "data" folder in the same directory as CloudSim.exe:

data/
├── instances.json      (Compute instances)
├── buckets/            (Storage files)
├── databases/          (Database files)
└── functions/          (Serverless functions)

This folder is created automatically on first run.

==============================================
SYSTEM REQUIREMENTS
==============================================

- Windows 10 or Windows 11
- 200 MB free disk space
- 4 GB RAM (recommended)
- No Python installation required
- No internet connection required

==============================================
EDUCATIONAL USE
==============================================

CloudSim is designed for:
✓ Learning cloud computing concepts
✓ Understanding AWS services
✓ Hands-on cloud practice
✓ Classroom demonstrations
✓ Experiment development
✓ Offline learning

Perfect for students who want to learn AWS without:
✗ Creating AWS accounts
✗ Paying for cloud resources
✗ Worrying about security/costs
✗ Needing internet access

==============================================
TIPS & TRICKS
==============================================

1. START WITH DASHBOARD
   - See your resource overview at a glance
   - Track what you've created

2. EXPERIMENT FREELY
   - No costs, no limits
   - Delete and recreate resources
   - Try different configurations

3. FOLLOW THE FLOW
   - Compute: Create instances → Start → Use → Stop → Delete
   - Storage: Create bucket → Upload files → Download → Delete
   - Database: Create DB → Create table → Insert data → Query
   - Serverless: Create function → Write code → Test with events

4. CHECK THE REGION SELECTOR
   - Educational feature teaching AWS regions
   - All regions are localhost variants

5. READ THE DOCS
   - Check the documentation folder for implementation details
   - Learn how each service works under the hood

==============================================
TROUBLESHOOTING
==============================================

APPLICATION WON'T START
→ Check Windows Defender (may need to allow)
→ Ensure you have Windows 10/11
→ Try running as Administrator

DATA NOT SAVING
→ Check write permissions in the folder
→ Don't run from C:\Program Files
→ Use Desktop or Documents folder

MISSING FEATURES
→ This is v1.0 - more features coming!
→ Check for updates on GitHub

ANTIVIRUS WARNING
→ PyInstaller executables sometimes flagged
→ Add to antivirus exclusions
→ CloudSim is open source and safe

==============================================
SUPPORT & RESOURCES
==============================================

📚 Documentation: Check the docs/ folder
🐛 Issues: Report on GitHub
📧 Contact: [Your Email/GitHub]
⭐ GitHub: [Your Repository URL]

==============================================
LICENSE
==============================================

MIT License

Copyright (c) 2026 CloudSim Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

==============================================
THANK YOU FOR USING CLOUDSIM!
==============================================

Happy learning! ☁️🚀
