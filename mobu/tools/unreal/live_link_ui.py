"""
MotionBuilder Live Link UI
Qt-based status window for UE5 connection monitoring
"""

from pyfbsdk import FBMessageBox
from PySide2 import QtWidgets, QtCore, QtGui
from core.logger import logger
from mobu.tools.unreal.live_link import get_live_link
import sys
import threading
from datetime import datetime

TOOL_NAME = "LiveLink Settings"


class ConnectionThread(QtCore.QThread):
    """Thread for non-blocking connection attempts"""

    connection_result = QtCore.Signal(bool, str)  # success, message

    def __init__(self, live_link, host=None, port=None):
        super(ConnectionThread, self).__init__()
        self.live_link = live_link
        self.host = host
        self.port = port

    def run(self):
        """Run connection attempt in thread"""
        try:
            success = self.live_link.connect(self.host, self.port)
            if success:
                message = f"Connected to {self.live_link.host}:{self.live_link.port}"
            else:
                message = "Failed to connect to Unreal Engine"
            self.connection_result.emit(success, message)
        except Exception as e:
            self.connection_result.emit(False, str(e))


class LogHandler:
    """Custom log handler that captures messages for the UI"""

    def __init__(self):
        self.messages = []
        self.max_messages = 1000

    def add_message(self, level, message):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.messages.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })

        # Keep only last N messages
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)

    def get_messages(self, level_filter=None):
        """Get messages, optionally filtered by level"""
        if level_filter:
            return [m for m in self.messages if m['level'] in level_filter]
        return self.messages

    def clear(self):
        """Clear all messages"""
        self.messages.clear()


class LiveLinkStatusWindow(QtWidgets.QDialog):
    """Live Link status and monitoring window"""

    def __init__(self, parent=None):
        super(LiveLinkStatusWindow, self).__init__(parent)

        self.live_link = get_live_link()
        self.log_handler = LogHandler()
        self.objects_sent = 0

        # Window setup
        self.setWindowTitle("MotionBuilder to UE5 - Live Link Monitor")
        self.setMinimumSize(600, 500)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)

        # Setup UI
        self._setup_ui()

        # Setup update timer
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self._update_status)
        self.update_timer.start(500)  # Update every 500ms

        # Initial status update
        self._update_status()

        # Log initial message
        self.log_handler.add_message('INFO', 'Live Link Monitor started')

        # Connection thread
        self.connection_thread = None

    def _setup_ui(self):
        """Setup the user interface"""
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setSpacing(10)

        # Title
        title_label = QtWidgets.QLabel("MotionBuilder → Unreal Engine 5")
        title_font = QtGui.QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # Status Frame
        status_frame = self._create_status_frame()
        main_layout.addWidget(status_frame)

        # Statistics Frame
        stats_frame = self._create_stats_frame()
        main_layout.addWidget(stats_frame)

        # Connection Controls
        controls_frame = self._create_controls_frame()
        main_layout.addWidget(controls_frame)

        # Log Viewer
        log_frame = self._create_log_frame()
        main_layout.addWidget(log_frame)

        # Bottom Buttons
        bottom_buttons = self._create_bottom_buttons()
        main_layout.addLayout(bottom_buttons)

        self.setLayout(main_layout)

    def _create_status_frame(self):
        """Create the connection status display"""
        frame = QtWidgets.QGroupBox("Connection Status")
        layout = QtWidgets.QVBoxLayout()

        # Status indicator
        status_layout = QtWidgets.QHBoxLayout()

        self.status_indicator = QtWidgets.QLabel("●")
        self.status_indicator.setStyleSheet("color: red; font-size: 24px;")
        status_layout.addWidget(self.status_indicator)

        self.status_label = QtWidgets.QLabel("Disconnected")
        status_font = QtGui.QFont()
        status_font.setPointSize(11)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Connection details
        details_layout = QtWidgets.QFormLayout()

        self.host_label = QtWidgets.QLabel(self.live_link.host)
        self.port_label = QtWidgets.QLabel(str(self.live_link.port))

        details_layout.addRow("Host:", self.host_label)
        details_layout.addRow("Port:", self.port_label)

        layout.addLayout(details_layout)

        frame.setLayout(layout)
        return frame

    def _create_stats_frame(self):
        """Create the statistics display"""
        frame = QtWidgets.QGroupBox("Statistics")
        layout = QtWidgets.QFormLayout()

        self.objects_sent_label = QtWidgets.QLabel("0")
        self.objects_sent_label.setStyleSheet("font-weight: bold; color: #4CAF50;")

        self.session_time_label = QtWidgets.QLabel("00:00:00")

        layout.addRow("Objects Sent:", self.objects_sent_label)
        layout.addRow("Session Time:", self.session_time_label)

        frame.setLayout(layout)
        return frame

    def _create_controls_frame(self):
        """Create connection control buttons"""
        frame = QtWidgets.QGroupBox("Connection Controls")
        layout = QtWidgets.QHBoxLayout()

        # Connect button
        self.connect_btn = QtWidgets.QPushButton("Connect")
        self.connect_btn.setMinimumHeight(35)
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.connect_btn.clicked.connect(self._on_connect)
        layout.addWidget(self.connect_btn)

        # Disconnect button
        self.disconnect_btn = QtWidgets.QPushButton("Disconnect")
        self.disconnect_btn.setMinimumHeight(35)
        self.disconnect_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.disconnect_btn.clicked.connect(self._on_disconnect)
        self.disconnect_btn.setEnabled(False)
        layout.addWidget(self.disconnect_btn)

        # Send Selected button
        self.send_btn = QtWidgets.QPushButton("Send Selected Objects")
        self.send_btn.setMinimumHeight(35)
        self.send_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.send_btn.clicked.connect(self._on_send_selected)
        self.send_btn.setEnabled(False)
        layout.addWidget(self.send_btn)

        frame.setLayout(layout)
        return frame

    def _create_log_frame(self):
        """Create the log viewer"""
        frame = QtWidgets.QGroupBox("Activity Log")
        layout = QtWidgets.QVBoxLayout()

        # Filter controls
        filter_layout = QtWidgets.QHBoxLayout()

        filter_label = QtWidgets.QLabel("Show:")
        filter_layout.addWidget(filter_label)

        self.filter_all = QtWidgets.QCheckBox("All")
        self.filter_all.setChecked(True)
        self.filter_all.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_all)

        self.filter_info = QtWidgets.QCheckBox("Info")
        self.filter_info.setChecked(True)
        self.filter_info.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_info)

        self.filter_warning = QtWidgets.QCheckBox("Warning")
        self.filter_warning.setChecked(True)
        self.filter_warning.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_warning)

        self.filter_error = QtWidgets.QCheckBox("Error")
        self.filter_error.setChecked(True)
        self.filter_error.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_error)

        filter_layout.addStretch()

        clear_log_btn = QtWidgets.QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self._on_clear_log)
        filter_layout.addWidget(clear_log_btn)

        layout.addLayout(filter_layout)

        # Log text area
        self.log_text = QtWidgets.QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, monospace;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.log_text)

        frame.setLayout(layout)
        return frame

    def _create_bottom_buttons(self):
        """Create bottom action buttons"""
        layout = QtWidgets.QHBoxLayout()

        help_btn = QtWidgets.QPushButton("Help")
        help_btn.clicked.connect(self._on_help)
        layout.addWidget(help_btn)

        layout.addStretch()

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return layout

    def _update_status(self):
        """Update the connection status display"""
        is_connected = self.live_link.is_connected()

        if is_connected:
            # Connected state
            self.status_indicator.setStyleSheet("color: #4CAF50; font-size: 24px;")
            self.status_label.setText("Connected to Unreal Engine")
            self.status_label.setStyleSheet("color: #4CAF50;")

            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.send_btn.setEnabled(True)
        else:
            # Disconnected state
            self.status_indicator.setStyleSheet("color: #f44336; font-size: 24px;")
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: #f44336;")

            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)
            self.send_btn.setEnabled(False)

        # Update statistics
        self.objects_sent_label.setText(str(self.objects_sent))

    def _on_connect(self):
        """Handle connect button click - non-blocking"""
        self._add_log('INFO', 'Connecting to Unreal Engine...')

        # Disable connect button during connection attempt
        self.connect_btn.setEnabled(False)
        self.connect_btn.setText("Connecting...")

        # Start connection in separate thread to avoid freezing
        self.connection_thread = ConnectionThread(self.live_link)
        self.connection_thread.connection_result.connect(self._on_connection_result)
        self.connection_thread.start()

    def _on_connection_result(self, success, message):
        """Handle connection thread result"""
        # Re-enable connect button
        self.connect_btn.setEnabled(True)
        self.connect_btn.setText("Connect")

        if success:
            self._add_log('INFO', message)
            self._update_status()
        else:
            self._add_log('ERROR', 'Failed to connect to Unreal Engine')
            self._add_log('WARNING', 'Make sure UE5 receiver is running')
            self._update_status()

            # Show error dialog
            FBMessageBox(
                "Connection Failed",
                "Failed to connect to Unreal Engine.\n\n"
                "Make sure:\n"
                "1. Unreal Engine 5 is running\n"
                "2. The receiver widget is started\n"
                f"3. Port {self.live_link.port} is not blocked\n\n"
                f"Details: {message}",
                "OK"
            )

    def _on_disconnect(self):
        """Handle disconnect button click"""
        self._add_log('INFO', 'Disconnecting from Unreal Engine...')
        self.live_link.disconnect()
        self._add_log('INFO', 'Disconnected')
        self._update_status()

    def _on_send_selected(self):
        """Handle send selected objects button click"""
        from pyfbsdk import FBModelList

        selected = FBModelList()
        from pyfbsdk import FBGetSelectedModels
        FBGetSelectedModels(selected)

        if len(selected) == 0:
            self._add_log('WARNING', 'No objects selected')
            FBMessageBox("No Selection", "Please select objects to send to Unreal Engine.", "OK")
            return

        self._add_log('INFO', f'Sending {len(selected)} object(s) to Unreal Engine...')

        success_count = 0
        for model in selected:
            if self.live_link.send_object(model):
                success_count += 1
                self.objects_sent += 1
                self._add_log('INFO', f'  → Sent: {model.Name}')
            else:
                self._add_log('ERROR', f'  ✗ Failed: {model.Name}')

        if success_count > 0:
            self._add_log('INFO', f'Successfully sent {success_count}/{len(selected)} object(s)')
        else:
            self._add_log('ERROR', 'Failed to send objects')

        self._update_status()

    def _on_filter_changed(self):
        """Handle log filter checkbox changes"""
        self._refresh_log_display()

    def _on_clear_log(self):
        """Clear the log"""
        self.log_handler.clear()
        self.log_text.clear()
        self._add_log('INFO', 'Log cleared')

    def _on_help(self):
        """Show help dialog"""
        help_text = """MotionBuilder to Unreal Engine 5 - Live Link Monitor

USAGE:
1. Click 'Connect' to establish connection with UE5
2. Select objects in MotionBuilder viewport
3. Click 'Send Selected Objects'
4. Objects appear in UE5 level!

REQUIREMENTS:
• Unreal Engine 5 must be running
• UE5 receiver widget must be started
• Both apps on same network (or localhost)

TROUBLESHOOTING:
• Check UE5 receiver is running (green status)
• Verify firewall allows port 9998
• Check activity log for errors

For detailed help, see:
mobu/tools/unreal/README_LIVE_LINK.md
"""
        FBMessageBox("Live Link Help", help_text, "OK")

    def _add_log(self, level, message):
        """Add a message to the log"""
        self.log_handler.add_message(level, message)
        logger.info(f"[LiveLink] {message}")
        self._refresh_log_display()

    def _refresh_log_display(self):
        """Refresh the log display based on filters"""
        # Determine which levels to show
        levels = []
        if self.filter_all.isChecked():
            levels = ['INFO', 'WARNING', 'ERROR']
        else:
            if self.filter_info.isChecked():
                levels.append('INFO')
            if self.filter_warning.isChecked():
                levels.append('WARNING')
            if self.filter_error.isChecked():
                levels.append('ERROR')

        # Get filtered messages
        messages = self.log_handler.get_messages(levels if levels else None)

        # Build HTML for colored output
        html = ""
        for msg in messages[-100:]:  # Show last 100 messages
            level = msg['level']
            timestamp = msg['timestamp']
            text = msg['message']

            # Color based on level
            if level == 'ERROR':
                color = '#f44336'
            elif level == 'WARNING':
                color = '#FFC107'
            else:
                color = '#4CAF50'

            html += f'<span style="color: #888;">[{timestamp}]</span> '
            html += f'<span style="color: {color}; font-weight: bold;">[{level}]</span> '
            html += f'<span style="color: #d4d4d4;">{text}</span><br>'

        self.log_text.setHtml(html)

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        """Handle window close"""
        self.update_timer.stop()

        # Clean up connection thread if running
        if self.connection_thread and self.connection_thread.isRunning():
            self.connection_thread.quit()
            self.connection_thread.wait()

        event.accept()


def execute(control, event):
    """Execute Live Link Monitor UI - called from menu"""
    logger.info("Opening Live Link Monitor...")

    try:
        # Create and show the window
        window = LiveLinkStatusWindow()
        window.exec_()

    except Exception as e:
        logger.error(f"Live Link Monitor error: {str(e)}")
        import traceback
        traceback.print_exc()
        FBMessageBox("Error", f"Failed to open Live Link Monitor:\n{str(e)}", "OK")


# For testing
if __name__ == "__main__":
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)

    window = LiveLinkStatusWindow()
    window.show()

    if not QtWidgets.QApplication.instance():
        sys.exit(app.exec_())
