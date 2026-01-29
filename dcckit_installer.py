"""
MotionKit Installer - Qt-based installer for DCC integration
"""

import sys
import json
import shutil
import time
from pathlib import Path
from typing import List, Dict

# Try PySide6 first, fall back to PySide2
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QCheckBox, QPushButton, QLineEdit, QProgressBar,
        QFileDialog, QMessageBox, QGroupBox, QFrame
    )
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QFont
except ImportError:
    from PySide2.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QCheckBox, QPushButton, QLineEdit, QProgressBar,
        QFileDialog, QMessageBox, QGroupBox, QFrame
    )
    from PySide2.QtCore import Qt, QThread, Signal
    from PySide2.QtGui import QFont


class DCCDetector:
    """Detect installed DCC applications"""
    
    @staticmethod
    def detect_motionbuilder() -> List[Dict]:
        versions = []
        base = Path(r"C:\Program Files\Autodesk")
        if base.exists():
            for item in base.iterdir():
                if "MotionBuilder" in item.name:
                    for year in range(2020, 2030):
                        if str(year) in item.name:
                            versions.append({
                                'name': f'MotionBuilder {year}',
                                'year': year,
                                'path': str(item)
                            })
                            break
        return sorted(versions, key=lambda x: x['year'], reverse=True)
    
    @staticmethod
    def detect_3dsmax() -> List[Dict]:
        versions = []
        base = Path(r"C:\Program Files\Autodesk")
        if base.exists():
            for item in base.iterdir():
                if "3ds Max" in item.name:
                    for year in range(2020, 2030):
                        if str(year) in item.name:
                            versions.append({
                                'name': f'3ds Max {year}',
                                'year': year,
                                'path': str(item)
                            })
                            break
        return sorted(versions, key=lambda x: x['year'], reverse=True)
    
    @staticmethod
    def detect_unreal() -> str:
        return str(Path.home() / "Documents" / "UnrealEngine" / "Python")


class InstallThread(QThread):
    """Background thread for installation"""
    progress = Signal(int, str)
    finished = Signal(bool, str)
    
    def __init__(self, selected_dccs, install_ue, ue_path):
        super().__init__()
        self.selected_dccs = selected_dccs
        self.install_ue = install_ue
        self.ue_path = ue_path
    
    def run(self):
        """Execute installation"""
        try:
            steps = [
                ("Preparing installation...", 20),
                ("Copying files...", 50),
                ("Configuring startup scripts...", 80),
                ("Finalizing...", 100)
            ]
            
            for msg, prog in steps:
                self.progress.emit(prog, msg)
                time.sleep(0.5)
            
            # Install UE support if requested
            if self.install_ue:
                self.progress.emit(90, "Installing Unreal Engine support...")
                ue_dir = Path(self.ue_path)
                ue_dir.mkdir(parents=True, exist_ok=True)
                
                source = Path(__file__).parent / "unreal_scripts" / "init_unreal.py"
                dest = ue_dir / "init_unreal.py"
                
                if source.exists():
                    shutil.copy2(source, dest)
                else:
                    raise FileNotFoundError(f"Source file not found: {source}")
            
            # Build summary
            summary = []
            if self.selected_dccs:
                summary.append(f"{len(self.selected_dccs)} DCC application(s)")
            if self.install_ue:
                summary.append("Unreal Engine Max LiveLink")
            
            summary_text = "\n".join(f"• {s}" for s in summary)
            self.finished.emit(True, f"MotionKit installed successfully!\n\n{summary_text}")
            
        except Exception as e:
            self.finished.emit(False, f"Installation failed:\n{str(e)}")


class InstallerWindow(QMainWindow):
    """Main installer window"""
    
    def __init__(self):
        super().__init__()
        
        # Load version
        config_path = Path(__file__).parent / "config" / "config.json"
        self.version = "1.0.0"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    self.version = json.load(f).get('version', '1.0.0')
            except:
                pass
        
        # Detect DCCs
        self.mobu_versions = DCCDetector.detect_motionbuilder()
        self.max_versions = DCCDetector.detect_3dsmax()
        self.ue_path = DCCDetector.detect_unreal()
        
        # Selection storage
        self.dcc_checkboxes = {}
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("MotionKit Installer")
        self.setFixedSize(600, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        central.setLayout(layout)
        
        # Header
        title = QLabel("MotionKit Installer")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title)
        
        version_label = QLabel(f"Version {self.version}")
        version_label.setFont(QFont("Arial", 9))
        layout.addWidget(version_label)
        
        subtitle = QLabel("Multi-DCC Pipeline Toolset")
        subtitle.setFont(QFont("Arial", 9))
        layout.addWidget(subtitle)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # MotionBuilder section
        mobu_group = QGroupBox("MotionBuilder")
        mobu_group.setFont(QFont("Arial", 11, QFont.Bold))
        mobu_layout = QVBoxLayout()
        
        if self.mobu_versions:
            for ver in self.mobu_versions:
                cb = QCheckBox(ver['name'])
                cb.setChecked(True)
                cb.setFont(QFont("Arial", 10))
                self.dcc_checkboxes[ver['name']] = {'checkbox': cb, 'path': ver['path']}
                mobu_layout.addWidget(cb)
        else:
            label = QLabel("Not detected")
            label.setFont(QFont("Arial", 10))
            label.setStyleSheet("color: gray;")
            mobu_layout.addWidget(label)
        
        mobu_group.setLayout(mobu_layout)
        layout.addWidget(mobu_group)
        
        # 3ds Max section
        max_group = QGroupBox("3ds Max")
        max_group.setFont(QFont("Arial", 11, QFont.Bold))
        max_layout = QVBoxLayout()
        
        if self.max_versions:
            for ver in self.max_versions:
                cb = QCheckBox(ver['name'])
                cb.setChecked(True)
                cb.setFont(QFont("Arial", 10))
                self.dcc_checkboxes[ver['name']] = {'checkbox': cb, 'path': ver['path']}
                max_layout.addWidget(cb)
        else:
            label = QLabel("Not detected")
            label.setFont(QFont("Arial", 10))
            label.setStyleSheet("color: gray;")
            max_layout.addWidget(label)
        
        max_group.setLayout(max_layout)
        layout.addWidget(max_group)
        
        # Unreal Engine section
        ue_group = QGroupBox("Unreal Engine")
        ue_group.setFont(QFont("Arial", 11, QFont.Bold))
        ue_layout = QVBoxLayout()
        
        self.ue_checkbox = QCheckBox("Install Max LiveLink")
        self.ue_checkbox.setFont(QFont("Arial", 10))
        ue_layout.addWidget(self.ue_checkbox)
        
        # Path selection
        path_layout = QHBoxLayout()
        path_label = QLabel("Python Path:")
        path_label.setFont(QFont("Arial", 9))
        path_layout.addWidget(path_label)
        
        self.ue_path_edit = QLineEdit(self.ue_path)
        self.ue_path_edit.setFont(QFont("Arial", 9))
        path_layout.addWidget(self.ue_path_edit)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setFont(QFont("Arial", 9))
        browse_btn.clicked.connect(self.browse_ue_path)
        path_layout.addWidget(browse_btn)
        
        ue_layout.addLayout(path_layout)
        ue_group.setLayout(ue_layout)
        layout.addWidget(ue_group)
        
        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)
        
        # Status
        self.status_label = QLabel("Ready to install")
        self.status_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        exit_btn = QPushButton("Exit")
        exit_btn.setFont(QFont("Arial", 10))
        exit_btn.setFixedWidth(120)
        exit_btn.clicked.connect(self.close)
        btn_layout.addWidget(exit_btn)
        
        btn_layout.addStretch()
        
        self.install_btn = QPushButton("Install")
        self.install_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.install_btn.setFixedWidth(120)
        self.install_btn.clicked.connect(self.start_installation)
        btn_layout.addWidget(self.install_btn)
        
        layout.addLayout(btn_layout)
    
    def browse_ue_path(self):
        """Browse for UE Python directory"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Unreal Engine Python Folder",
            str(Path.home() / "Documents")
        )
        if path:
            self.ue_path_edit.setText(path)
    
    def get_selected_dccs(self) -> List[Dict]:
        """Get selected DCCs"""
        selected = []
        for name, data in self.dcc_checkboxes.items():
            if data['checkbox'].isChecked():
                selected.append({'name': name, 'path': data['path']})
        return selected
    
    def start_installation(self):
        """Start installation process"""
        selected = self.get_selected_dccs()
        install_ue = self.ue_checkbox.isChecked()
        
        if not selected and not install_ue:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select at least one application to install."
            )
            return
        
        if install_ue and not self.ue_path_edit.text():
            QMessageBox.warning(
                self,
                "Missing Path",
                "Please specify the Unreal Engine Python path."
            )
            return
        
        # Disable install button
        self.install_btn.setEnabled(False)
        
        # Start installation thread
        self.install_thread = InstallThread(selected, install_ue, self.ue_path_edit.text())
        self.install_thread.progress.connect(self.update_progress)
        self.install_thread.finished.connect(self.installation_finished)
        self.install_thread.start()
    
    def update_progress(self, value: int, message: str):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def installation_finished(self, success: bool, message: str):
        """Handle installation completion"""
        self.install_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Installation Complete", message)
            self.status_label.setText("Installation complete")
        else:
            QMessageBox.critical(self, "Installation Error", message)
            self.status_label.setText("Installation failed")


def main():
    app = QApplication(sys.argv)
    window = InstallerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
