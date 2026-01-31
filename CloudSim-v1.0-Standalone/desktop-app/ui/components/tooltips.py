"""
Educational Tooltips - Cloud concept explanations on hover
Helps users understand AWS/cloud terminology
"""

from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPalette, QColor
from ui.design_system import Colors, Fonts


class CloudTooltip(QLabel):
    """
    Rich tooltip with cloud concept explanations
    Appears on hover with smooth fade-in animation
    """
    
    # Cloud concept definitions
    CONCEPTS = {
        # Compute
        'instance': {
            'term': 'EC2 Instance',
            'definition': 'A virtual server in the cloud. Like renting a computer that runs 24/7.',
            'example': 'Use for web servers, databases, or any application'
        },
        'instance_type': {
            'term': 'Instance Type',
            'definition': 'The hardware configuration (CPU, RAM, storage) of your virtual server.',
            'example': 't2.micro = 1 vCPU, 1GB RAM (free tier eligible)'
        },
        'ami': {
            'term': 'Amazon Machine Image',
            'definition': 'A template that contains the software configuration (OS, apps, settings).',
            'example': 'Like a snapshot of a configured computer you can launch instantly'
        },
        
        # Storage
        's3': {
            'term': 'S3 (Simple Storage Service)',
            'definition': 'Object storage for any amount of data. Accessible from anywhere on the web.',
            'example': 'Store backups, images, videos, logs - anything'
        },
        'bucket': {
            'term': 'S3 Bucket',
            'definition': 'A container for storing objects (files) in S3. Each bucket has a unique name.',
            'example': 'Like a top-level folder that holds all your files'
        },
        'object': {
            'term': 'S3 Object',
            'definition': 'Any file stored in S3. Can be up to 5TB in size.',
            'example': 'Photos, videos, documents, backups, logs'
        },
        
        # Volumes
        'ebs': {
            'term': 'EBS (Elastic Block Store)',
            'definition': 'Persistent block storage volumes for EC2 instances. Like external hard drives.',
            'example': 'Stores your database data, application files'
        },
        'volume': {
            'term': 'EBS Volume',
            'definition': 'A virtual hard drive that attaches to an EC2 instance.',
            'example': 'Root volume (OS) or data volumes for databases'
        },
        'snapshot': {
            'term': 'EBS Snapshot',
            'definition': 'A backup of your EBS volume at a specific point in time.',
            'example': 'Like taking a photo of your hard drive to restore later'
        },
        
        # Database
        'rds': {
            'term': 'RDS (Relational Database Service)',
            'definition': 'Managed database service. AWS handles backups, patching, scaling.',
            'example': 'Run MySQL, PostgreSQL, Oracle without managing servers'
        },
        'db_instance': {
            'term': 'Database Instance',
            'definition': 'An isolated database environment running in the cloud.',
            'example': 'Your application\'s production database'
        },
        'read_replica': {
            'term': 'Read Replica',
            'definition': 'A copy of your database that handles read queries. Improves performance.',
            'example': 'Offload reporting queries from your main database'
        },
        
        # Serverless
        'lambda': {
            'term': 'AWS Lambda',
            'definition': 'Run code without managing servers. Pay only for compute time you use.',
            'example': 'Process image uploads, respond to API requests'
        },
        'function': {
            'term': 'Lambda Function',
            'definition': 'Your code packaged to run in Lambda. Triggered by events.',
            'example': 'Resize images when uploaded to S3'
        },
        'trigger': {
            'term': 'Event Trigger',
            'definition': 'Something that causes your Lambda function to execute.',
            'example': 'S3 upload, API request, scheduled time'
        },
        
        # IAM
        'iam': {
            'term': 'IAM (Identity & Access Management)',
            'definition': 'Controls who can access your AWS resources and what they can do.',
            'example': 'Give developers read-only access to S3'
        },
        'role': {
            'term': 'IAM Role',
            'definition': 'A set of permissions that can be assumed by AWS services or users.',
            'example': 'Allow EC2 instance to read from S3'
        },
        'policy': {
            'term': 'IAM Policy',
            'definition': 'A document defining permissions (allow/deny actions on resources).',
            'example': 'Allow: s3:GetObject on bucket/photos/*'
        },
        
        # Network
        'vpc': {
            'term': 'VPC (Virtual Private Cloud)',
            'definition': 'Your own isolated network in AWS. Like your own data center.',
            'example': 'Secure network for your applications'
        },
        'subnet': {
            'term': 'Subnet',
            'definition': 'A range of IP addresses in your VPC. Can be public or private.',
            'example': 'Public subnet for web servers, private for databases'
        },
        'security_group': {
            'term': 'Security Group',
            'definition': 'Virtual firewall controlling inbound/outbound traffic.',
            'example': 'Allow HTTP (port 80) from anywhere, SSH only from your IP'
        },
        
        # General
        'region': {
            'term': 'AWS Region',
            'definition': 'A physical location around the world where AWS has data centers.',
            'example': 'us-east-1 (Virginia), eu-west-1 (Ireland)'
        },
        'availability_zone': {
            'term': 'Availability Zone',
            'definition': 'Isolated locations within a region. For high availability.',
            'example': 'Run instances in multiple AZs to survive data center failure'
        },
        'tags': {
            'term': 'Resource Tags',
            'definition': 'Key-value pairs for organizing and tracking resources.',
            'example': 'Environment: Production, Owner: DevTeam'
        },
    }
    
    _instance = None
    
    def __init__(self, content=None, parent=None):
        """
        Initialize CloudTooltip
        
        Args:
            content: Either a concept_key string or a dict with {title, description, details}
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWordWrap(True)
        self.setMaximumWidth(400)
        self._setup_style()
        self._setup_animation()
        
        # Auto-hide timer
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_animated)
        
        # Set initial content if provided
        if content:
            if isinstance(content, dict):
                self._set_custom_content(content)
            elif isinstance(content, str):
                self._set_concept_content(content)
    
    def _setup_style(self):
        """Style the tooltip with modern design"""
        self.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e293b, stop:1 #1a2535);
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.ACCENT};
                border-radius: 8px;
                padding: 16px;
                font-size: {Fonts.SMALL};
                line-height: 1.6;
            }}
        """)
        
        # Add drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
    
    def _setup_animation(self):
        """Setup fade-in animation"""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def _set_custom_content(self, content: dict):
        """Set custom tooltip content from dict"""
        title = content.get('title', '')
        description = content.get('description', '')
        details = content.get('details', [])
        
        # Format tooltip text
        html = f"""
        <div style='line-height: 1.6;'>
            <p style='margin: 0 0 8px 0;'>
                <span style='color: {Colors.ACCENT}; font-weight: 600; font-size: {Fonts.HEADING};'>
                    {title}
                </span>
            </p>
            <p style='margin: 0 0 12px 0; color: {Colors.TEXT_SECONDARY};'>
                {description}
            </p>
        """
        
        if details:
            html += f"""
            <div style='padding: 12px; background: rgba(99, 102, 241, 0.1); 
                      border-left: 2px solid {Colors.ACCENT}; border-radius: 4px;'>
            """
            for detail in details:
                html += f"<p style='margin: 4px 0; color: {Colors.TEXT_MUTED}; font-size: {Fonts.SMALL};'>{detail}</p>"
            html += "</div>"
        
        html += "</div>"
        
        self.setText(html)
        self.adjustSize()
    
    def _set_concept_content(self, concept_key: str):
        """Set content from predefined concept"""
        concept = self.CONCEPTS.get(concept_key)
        if not concept:
            return
        
        # Format tooltip text
        html = f"""
        <div style='line-height: 1.6;'>
            <p style='margin: 0 0 8px 0;'>
                <span style='color: {Colors.ACCENT}; font-weight: 600; font-size: {Fonts.HEADING};'>
                    {concept['term']}
                </span>
            </p>
            <p style='margin: 0 0 12px 0; color: {Colors.TEXT_SECONDARY};'>
                {concept['definition']}
            </p>
            <p style='margin: 0; padding: 8px 12px; background: rgba(99, 102, 241, 0.1); 
                      border-left: 2px solid {Colors.ACCENT}; border-radius: 4px; 
                      color: {Colors.TEXT_MUTED}; font-size: {Fonts.SMALL};'>
                <b>Example:</b> {concept['example']}
            </p>
        </div>
        """
        
        self.setText(html)
        self.adjustSize()
    
    def show_at_widget(self, widget):
        """Show tooltip at widget position"""
        position = widget.mapToGlobal(QPoint(0, widget.height()))
        self.move(position.x() + 15, position.y() + 5)
        
        # Animate in
        self.setWindowOpacity(0)
        self.show()
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        
        # Auto-hide after 10 seconds
        self.hide_timer.start(10000)
    
    def show_concept(self, concept_key: str, position: QPoint):
        """Show tooltip for a cloud concept"""
        concept = self.CONCEPTS.get(concept_key)
        if not concept:
            return
        
        # Format tooltip text
        html = f"""
        <div style='line-height: 1.6;'>
            <p style='margin: 0 0 8px 0;'>
                <span style='color: {Colors.ACCENT}; font-weight: 600; font-size: {Fonts.HEADING};'>
                    {concept['term']}
                </span>
            </p>
            <p style='margin: 0 0 12px 0; color: {Colors.TEXT_SECONDARY};'>
                {concept['definition']}
            </p>
            <p style='margin: 0; padding: 8px 12px; background: rgba(99, 102, 241, 0.1); 
                      border-left: 2px solid {Colors.ACCENT}; border-radius: 4px; 
                      color: {Colors.TEXT_MUTED}; font-size: {Fonts.SMALL};'>
                <b>Example:</b> {concept['example']}
            </p>
        </div>
        """
        
        self.setText(html)
        self.adjustSize()
        
        # Position near cursor with offset
        self.move(position.x() + 15, position.y() + 15)
        
        # Animate in
        self.setWindowOpacity(0)
        self.show()
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()
        
        # Auto-hide after 8 seconds
        self.hide_timer.start(8000)
    
    def hide_animated(self):
        """Fade out and hide"""
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.finished.connect(self.hide)
        self.animation.start()
    
    @classmethod
    def instance(cls, parent=None):
        """Singleton instance"""
        if cls._instance is None:
            cls._instance = cls(parent)
        return cls._instance


def show_cloud_tooltip(concept_key: str, position: QPoint, parent=None):
    """
    Convenience function to show a cloud concept tooltip
    
    Args:
        concept_key: Key from CloudTooltip.CONCEPTS
        position: Global position to show tooltip
        parent: Parent widget
    """
    tooltip = CloudTooltip.instance(parent)
    tooltip.show_concept(concept_key, position)


def add_tooltip_to_widget(widget, concept_key: str):
    """
    Add hover tooltip to a widget
    
    Args:
        widget: QWidget to add tooltip to
        concept_key: Concept key to show on hover
    """
    def on_enter(event):
        pos = widget.mapToGlobal(QPoint(0, widget.height()))
        show_cloud_tooltip(concept_key, pos, widget.window())
    
    def on_leave(event):
        tooltip = CloudTooltip.instance()
        QTimer.singleShot(100, tooltip.hide_animated)
    
    widget.enterEvent = on_enter
    widget.leaveEvent = on_leave
