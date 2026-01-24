"""
Enhanced Activity Log View with Billing and Usage Analytics
CloudTrail-style activity logging with cost tracking and educational explanations
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
    QHeaderView, QGroupBox, QScrollArea, QFrame, QTextEdit,
    QDialog, QDialogButtonBox, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPainter, QColor, QPen
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis
from services.billing_service import billing_service, COST_EXPLANATIONS
from core.session_manager import session_manager
from ui.design_system import Colors, Fonts, Spacing
from ui.components.notifications import NotificationManager
from datetime import datetime, timedelta
import secrets


class CostMetricCard(QWidget):
    """Card displaying a cost metric with educational tooltip"""
    
    def __init__(self, title: str, value: str, subtitle: str = "", explanation: str = ""):
        super().__init__()
        self.explanation = explanation
        self.setup_ui(title, value, subtitle)
    
    def setup_ui(self, title: str, value: str, subtitle: str):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {Fonts.SMALL};")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 32px; font-weight: bold;")
        layout.addWidget(value_label)
        
        # Subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {Fonts.SMALL};")
            layout.addWidget(subtitle_label)
        
        # Learn more button
        if self.explanation:
            learn_btn = QPushButton("ℹ️ Learn More")
            learn_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {Colors.PRIMARY};
                    border: none;
                    padding: 4px;
                    font-size: {Fonts.SMALL};
                    text-align: left;
                }}
                QPushButton:hover {{
                    color: {Colors.PRIMARY_LIGHT};
                    text-decoration: underline;
                }}
            """)
            learn_btn.clicked.connect(self.show_explanation)
            layout.addWidget(learn_btn)
        
        self.setLayout(layout)
        self.setStyleSheet(f"""
            CostMetricCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.SURFACE}, stop:1 rgba(99, 102, 241, 0.05));
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
    
    def show_explanation(self):
        """Show educational explanation dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Cost Explanation")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        text_edit = QTextEdit()
        text_edit.setMarkdown(self.explanation)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.BACKGROUND};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 16px;
                font-size: {Fonts.BODY};
            }}
        """)
        layout.addWidget(text_edit)
        
        # Close button
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(dialog.close)
        layout.addWidget(btn_box)
        
        dialog.setLayout(layout)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BACKGROUND};
            }}
        """)
        dialog.exec()


class UsageChart(QChartView):
    """Usage/cost chart with educational tooltips"""
    
    def __init__(self):
        super().__init__()
        self.setup_chart()
    
    def setup_chart(self):
        """Setup the cost chart"""
        self.chart = QChart()
        self.chart.setTitle("Daily Cost Breakdown (Last 30 Days)")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.setTheme(QChart.ChartThemeDark)
        
        # Create series
        self.series = QLineSeries()
        self.series.setName("Daily Cost ($)")
        
        # Load data
        self.update_data()
        
        # Style
        pen = QPen(QColor(99, 102, 241))
        pen.setWidth(3)
        self.series.setPen(pen)
        
        self.chart.addSeries(self.series)
        
        # Axes
        axis_x = QDateTimeAxis()
        axis_x.setFormat("MMM dd")
        axis_x.setTitleText("Date")
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        self.series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("Cost ($)")
        axis_y.setLabelFormat("$%.2f")
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        self.series.attachAxis(axis_y)
        
        self.setChart(self.chart)
        self.setRenderHint(QPainter.Antialiasing)
        
        # Style
        self.setStyleSheet(f"""
            QChartView {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
    
    def update_data(self):
        """Update chart with latest billing data"""
        self.series.clear()
        
        daily_costs = billing_service.get_daily_costs(30)
        
        for date, cost in daily_costs:
            timestamp = date.timestamp() * 1000  # Convert to milliseconds
            self.series.append(timestamp, cost)


class ActivityDetailDialog(QDialog):
    """Dialog showing detailed activity log information"""
    
    def __init__(self, activity_log, parent=None):
        super().__init__(parent)
        self.activity_log = activity_log
        self.setWindowTitle(f"Activity Details - {activity_log.event_id}")
        self.setMinimumSize(700, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Event details
        details_text = f"""
**Event ID:** {self.activity_log.event_id}

**Timestamp:** {self.activity_log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

**User:** {self.activity_log.user}

**Service:** {self.activity_log.service}

**Action:** {self.activity_log.action}

**Resource Type:** {self.activity_log.resource_type}

**Resource ID:** {self.activity_log.resource_id}

**Resource Name:** {self.activity_log.resource_name}

**Region:** {self.activity_log.region}

**Status:** {self.activity_log.status}

**Cost Impact:** ${self.activity_log.cost_impact:.4f}

---

### Additional Details

"""
        
        # Add details
        if self.activity_log.details:
            for key, value in self.activity_log.details.items():
                details_text += f"**{key}:** {value}\n\n"
        else:
            details_text += "*No additional details*\n"
        
        # Add educational explanation
        service_key = self.activity_log.service.lower()
        if service_key in COST_EXPLANATIONS:
            details_text += f"\n---\n\n### 📚 Understanding {self.activity_log.service} Costs\n\n"
            details_text += COST_EXPLANATIONS[service_key]
        
        text_edit = QTextEdit()
        text_edit.setMarkdown(details_text)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Colors.BACKGROUND};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 16px;
                font-size: {Fonts.BODY};
            }}
        """)
        layout.addWidget(text_edit)
        
        # Close button
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.close)
        layout.addWidget(btn_box)
        
        self.setLayout(layout)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BACKGROUND};
            }}
        """)


class EnhancedActivityLogView(QWidget):
    """Enhanced activity log view with billing and usage analytics"""
    
    def __init__(self):
        super().__init__()
        self.current_service_filter = "All"
        self.setup_ui()
        
        # Defer data loading to after UI is fully initialized
        QTimer.singleShot(100, self._safe_load_data)
        
        # Auto-refresh every 10 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._safe_load_data)
        self.refresh_timer.start(10000)
    
    def _safe_load_data(self):
        """Safely load data with error handling"""
        try:
            self.load_data()
        except Exception as e:
            print(f"Error loading activity log data: {e}")
            # Continue anyway - don't block the app
    
    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 Activity & Cost Analytics")
        title.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 28px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.PRIMARY};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {Colors.PRIMARY_LIGHT};
            }}
        """)
        refresh_btn.clicked.connect(self.load_data)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Cost metrics section
        metrics_layout = QHBoxLayout()
        
        self.cost_cards = {
            "month_to_date": CostMetricCard(
                "Month-to-Date Cost",
                "$0.00",
                "",
                COST_EXPLANATIONS.get("general", "")
            ),
            "forecasted": CostMetricCard(
                "Forecasted Monthly Cost",
                "$0.00",
                "Based on current usage",
                """
**Forecasted Cost Calculation**

This estimate projects your end-of-month cost based on:
- Current daily spending rate
- Days elapsed in the month
- Extrapolation to full month

💡 **Note**: Actual costs may vary based on:
- Resource usage changes
- Starting/stopping resources
- Data transfer patterns
"""
            ),
            "active_resources": CostMetricCard(
                "Active Resources",
                "0",
                "Currently running",
                """
**Active Resources**

Resources that are currently:
- Running (EC2 instances, RDS databases)
- Storing data (S3 buckets, EBS volumes)
- Configured (Lambda functions)

💡 **Tip**: Stop resources when not in use to reduce costs!
"""
            ),
            "activity_count": CostMetricCard(
                "Total Activities",
                "0",
                "This month",
                """
**Activity Count**

Tracks all actions performed:
- Resource creation/deletion
- Configuration changes
- API calls
- Permission changes

Similar to AWS CloudTrail event logging.
"""
            )
        }
        
        for card in self.cost_cards.values():
            metrics_layout.addWidget(card)
        
        main_layout.addLayout(metrics_layout)
        
        # Usage chart
        chart_group = QGroupBox("📈 Cost Trend")
        chart_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                padding: 20px;
                margin-top: 10px;
                font-size: {Fonts.HEADING};
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }}
        """)
        chart_layout = QVBoxLayout()
        
        self.usage_chart = UsageChart()
        chart_layout.addWidget(self.usage_chart)
        
        chart_group.setLayout(chart_layout)
        main_layout.addWidget(chart_group)
        
        # Activity log section
        log_group = QGroupBox("📋 Activity Timeline (CloudTrail)")
        log_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                padding: 20px;
                margin-top: 10px;
                font-size: {Fonts.HEADING};
                font-weight: bold;
                color: {Colors.TEXT_PRIMARY};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }}
        """)
        log_layout = QVBoxLayout()
        
        # Filters
        filter_layout = QHBoxLayout()
        
        filter_label = QLabel("Filter by Service:")
        filter_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: {Fonts.BODY};")
        filter_layout.addWidget(filter_label)
        
        self.service_filter = QComboBox()
        self.service_filter.addItem("All")
        self.service_filter.addItems(["EC2", "S3", "EBS", "RDS", "Lambda", "IAM"])
        self.service_filter.currentTextChanged.connect(self.apply_filter)
        self.service_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {Colors.BACKGROUND};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px;
                min-width: 150px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox:hover {{
                border-color: {Colors.PRIMARY};
            }}
        """)
        filter_layout.addWidget(self.service_filter)
        
        filter_layout.addStretch()
        
        # Search
        search_label = QLabel("Search:")
        search_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: {Fonts.BODY};")
        filter_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search activities...")
        self.search_input.textChanged.connect(self.apply_filter)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.BACKGROUND};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px;
                min-width: 250px;
            }}
            QLineEdit:focus {{
                border-color: {Colors.PRIMARY};
            }}
        """)
        filter_layout.addWidget(self.search_input)
        
        log_layout.addLayout(filter_layout)
        
        # Activity table
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(7)
        self.activity_table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Service", "Action", "Resource", "Status", "Cost Impact"
        ])
        
        # Set column widths
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        self.activity_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.activity_table.setSelectionMode(QTableWidget.SingleSelection)
        self.activity_table.doubleClicked.connect(self.show_activity_details)
        
        self.activity_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {Colors.BACKGROUND};
                alternate-background-color: {Colors.SURFACE};
                gridline-color: {Colors.BORDER};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: 10px;
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.PRIMARY};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {Colors.SURFACE};
                color: {Colors.TEXT_PRIMARY};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {Colors.PRIMARY};
                font-weight: bold;
            }}
        """)
        
        log_layout.addWidget(self.activity_table)
        
        # Hint label
        hint = QLabel("💡 Tip: Double-click any activity to see detailed information and cost explanations")
        hint.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-size: {Fonts.SMALL}; font-style: italic;")
        log_layout.addWidget(hint)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        self.setLayout(main_layout)
        self.setStyleSheet(f"background-color: {Colors.BACKGROUND};")
    
    def load_data(self):
        """Load billing and activity data"""
        # Get billing summary
        summary = billing_service.get_current_month_summary()
        
        # Update cost cards
        self.cost_cards["month_to_date"].findChild(QLabel, "", Qt.FindChildrenRecursively).setText(
            f"${summary.total_cost:.2f}"
        )
        
        # Update card values (find value labels)
        for card_key, card in self.cost_cards.items():
            value_label = None
            for child in card.findChildren(QLabel):
                if "32px" in child.styleSheet():  # Value label has 32px font
                    value_label = child
                    break
            
            if value_label:
                if card_key == "month_to_date":
                    value_label.setText(f"${summary.total_cost:.2f}")
                elif card_key == "forecasted":
                    value_label.setText(f"${summary.forecasted_monthly_cost:.2f}")
                elif card_key == "active_resources":
                    value_label.setText(str(summary.total_resources))
                elif card_key == "activity_count":
                    # Limit to reasonable number to avoid hanging
                    total_activities = len(billing_service.get_activity_logs(limit=100))
                    value_label.setText(f"{total_activities}+")
        
        # Update chart
        self.usage_chart.update_data()
        
        # Load activity logs
        self.apply_filter()
    
    def apply_filter(self):
        """Apply service filter to activity logs"""
        service_filter = self.service_filter.currentText()
        search_text = self.search_input.text().lower()
        
        # Get filtered logs
        if service_filter == "All":
            logs = billing_service.get_activity_logs(limit=100)
        else:
            logs = billing_service.get_activity_logs(service=service_filter, limit=100)
        
        # Apply search filter
        if search_text:
            logs = [
                log for log in logs
                if search_text in log.action.lower() or
                   search_text in log.resource_name.lower() or
                   search_text in log.user.lower()
            ]
        
        # Update table
        self.activity_table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            # Timestamp
            time_item = QTableWidgetItem(log.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            self.activity_table.setItem(row, 0, time_item)
            
            # User
            user_item = QTableWidgetItem(log.user)
            self.activity_table.setItem(row, 1, user_item)
            
            # Service
            service_item = QTableWidgetItem(log.service)
            self.activity_table.setItem(row, 2, service_item)
            
            # Action
            action_item = QTableWidgetItem(log.action)
            self.activity_table.setItem(row, 3, action_item)
            
            # Resource
            resource_item = QTableWidgetItem(f"{log.resource_name} ({log.resource_id})")
            self.activity_table.setItem(row, 4, resource_item)
            
            # Status
            status_item = QTableWidgetItem(log.status)
            if log.status == "success":
                status_item.setForeground(QColor(34, 197, 94))  # Green
            elif log.status == "failed":
                status_item.setForeground(QColor(239, 68, 68))  # Red
            else:
                status_item.setForeground(QColor(234, 179, 8))  # Yellow
            self.activity_table.setItem(row, 5, status_item)
            
            # Cost impact
            cost_item = QTableWidgetItem(f"${log.cost_impact:.4f}")
            if log.cost_impact > 0:
                cost_item.setForeground(QColor(99, 102, 241))  # Blue
            self.activity_table.setItem(row, 6, cost_item)
            
            # Store log object for details dialog
            self.activity_table.item(row, 0).setData(Qt.UserRole, log)
    
    def show_activity_details(self, index):
        """Show detailed activity information"""
        row = index.row()
        log = self.activity_table.item(row, 0).data(Qt.UserRole)
        
        if log:
            dialog = ActivityDetailDialog(log, self)
            dialog.exec()


# For backward compatibility
ActivityLogView = EnhancedActivityLogView
