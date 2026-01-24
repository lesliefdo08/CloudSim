"""
Demo: Dashboard Storytelling Enhancements
Standalone test of sparklines, insights, and ghost entries
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt

# Add parent directory to path
sys.path.insert(0, '.')

from ui.components.sparkline import SparklineChart, InsightCard, GhostTimelineEntry


class DemoWindow(QMainWindow):
    """Demo window showing storytelling components"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard Storytelling Demo - CloudSim")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background: #0f172a;")
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)
        
        # Title
        title = QLabel("📊 Dashboard Storytelling Components")
        title.setStyleSheet("""
            color: #f8fafc;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        # Section 1: Sparklines
        section1 = QLabel("1. Sparkline Charts (Trend Visualization)")
        section1.setStyleSheet("color: #cbd5e1; font-size: 16px; font-weight: 600; margin-top: 10px;")
        layout.addWidget(section1)
        
        # Growing trend
        sparkline1_label = QLabel("Instance count trend (growing):")
        sparkline1_label.setStyleSheet("color: #94a3b8; font-size: 13px;")
        layout.addWidget(sparkline1_label)
        
        sparkline1 = SparklineChart([3, 4, 3, 5, 6, 7, 8, 9, 10, 11])
        layout.addWidget(sparkline1)
        
        # Declining trend
        sparkline2_label = QLabel("Storage usage trend (declining):")
        sparkline2_label.setStyleSheet("color: #94a3b8; font-size: 13px;")
        layout.addWidget(sparkline2_label)
        
        sparkline2 = SparklineChart([100, 95, 90, 85, 80, 75, 70, 65, 60, 55])
        layout.addWidget(sparkline2)
        
        # Stable trend
        sparkline3_label = QLabel("Database connections (stable):")
        sparkline3_label.setStyleSheet("color: #94a3b8; font-size: 13px;")
        layout.addWidget(sparkline3_label)
        
        sparkline3 = SparklineChart([50, 51, 50, 49, 50, 51, 50, 49, 50, 51])
        layout.addWidget(sparkline3)
        
        # Section 2: Insight Cards
        section2 = QLabel("2. Insight Cards (Actionable Recommendations)")
        section2.setStyleSheet("color: #cbd5e1; font-size: 16px; font-weight: 600; margin-top: 20px;")
        layout.addWidget(section2)
        
        # Warning insight
        warning_insight = InsightCard(
            icon="⚠️",
            title="21 stopped instances — potential waste",
            message="Stopped instances still incur storage costs. Consider terminating unused instances to reduce monthly expenses.",
            severity="warning"
        )
        layout.addWidget(warning_insight)
        
        # Info insight
        info_insight = InsightCard(
            icon="💰",
            title="7 running instances detected",
            message="Review instance sizes and consider right-sizing to optimize costs. Over-provisioned instances waste budget.",
            severity="info"
        )
        layout.addWidget(info_insight)
        
        # Success insight
        success_insight = InsightCard(
            icon="🚀",
            title="Ready to build something amazing?",
            message="Start by launching your first EC2 instance or creating an S3 bucket. Quick actions available in the sidebar.",
            severity="success"
        )
        layout.addWidget(success_insight)
        
        # Section 3: Ghost Timeline
        section3 = QLabel("3. Ghost Timeline Entries (Empty State)")
        section3.setStyleSheet("color: #cbd5e1; font-size: 16px; font-weight: 600; margin-top: 20px;")
        layout.addWidget(section3)
        
        ghost_container = QWidget()
        ghost_container.setStyleSheet("""
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 12px;
        """)
        ghost_layout = QVBoxLayout(ghost_container)
        ghost_layout.setSpacing(8)
        
        for i in range(3):
            ghost_entry = GhostTimelineEntry("Awaiting activity…")
            ghost_layout.addWidget(ghost_entry)
        
        layout.addWidget(ghost_container)
        
        layout.addStretch()
        
        # Footer
        footer = QLabel("💡 These components make the dashboard tell a story, not just show numbers.")
        footer.setStyleSheet("color: #64748b; font-size: 12px; font-style: italic; margin-top: 10px;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    window = DemoWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
