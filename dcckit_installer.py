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
        QFileDialog, QMessageBox, QGroupBox, QFrame, QComboBox
    )
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QFont
except ImportError:
    from PySide2.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QCheckBox, QPushButton, QLineEdit, QProgressBar,
        QFileDialog, QMessageBox, QGroupBox, QFrame, QComboBox
    )
    from PySide2.QtCore import Qt, QThread, Signal
    from PySide2.QtGui import QFont


# Translations
TRANSLATIONS = {
    'en': {
        'title': 'MotionKit Installer',
        'version': 'Version',
        'subtitle': 'Multi-DCC Pipeline Toolset',
        'language': 'Language:',
        'detected': 'Detected:',
        'install_to': 'Install To:',
        'motionbuilder': 'MotionBuilder',
        'max': '3ds Max',
        'unreal': 'Unreal Engine',
        'install_livelink': 'Install Max LiveLink',
        'python_path': 'Python Path:',
        'browse': 'Browse',
        'not_detected': 'Not detected',
        'ready': 'Ready to install',
        'exit': 'Exit',
        'install': 'Install',
        'no_selection': 'No Selection',
        'no_selection_msg': 'Please select at least one application to install.',
        'missing_path': 'Missing Path',
        'missing_path_msg': 'Please specify the Unreal Engine Python path.',
        'preparing': 'Preparing installation...',
        'copying': 'Copying files...',
        'configuring': 'Configuring startup scripts...',
        'finalizing': 'Finalizing...',
        'installing_ue': 'Installing Unreal Engine support...',
        'complete': 'Installation Complete',
        'complete_msg': 'MotionKit installed successfully!',
        'error': 'Installation Error',
        'error_msg': 'Installation failed:',
        'install_complete': 'Installation complete',
        'install_failed': 'Installation failed',
        'dcc_apps': 'DCC application(s)',
        'ue_livelink': 'Unreal Engine Max LiveLink'
    },
    'zh': {
        'title': 'MotionKit 安装程序',
        'version': '版本',
        'subtitle': '多DCC流程工具集',
        'language': '语言:',
        'detected': '检测到:',
        'install_to': '安装到:',
        'motionbuilder': 'MotionBuilder',
        'max': '3ds Max',
        'unreal': '虚幻引擎',
        'install_livelink': '安装 Max LiveLink',
        'python_path': 'Python 路径:',
        'browse': '浏览',
        'not_detected': '未检测到',
        'ready': '准备安装',
        'exit': '退出',
        'install': '安装',
        'no_selection': '未选择',
        'no_selection_msg': '请至少选择一个要安装的应用程序。',
        'missing_path': '缺少路径',
        'missing_path_msg': '请指定虚幻引擎 Python 路径。',
        'preparing': '准备安装中...',
        'copying': '正在复制文件...',
        'configuring': '正在配置启动脚本...',
        'finalizing': '正在完成...',
        'installing_ue': '正在安装虚幻引擎支持...',
        'complete': '安装完成',
        'complete_msg': 'MotionKit 安装成功！',
        'error': '安装错误',
        'error_msg': '安装失败:',
        'install_complete': '安装完成',
        'install_failed': '安装失败',
        'dcc_apps': '个DCC应用程序',
        'ue_livelink': '虚幻引擎 Max LiveLink'
    },
    'ko': {
        'title': 'MotionKit 설치 프로그램',
        'version': '버전',
        'subtitle': '다중 DCC 파이프라인 도구 세트',
        'language': '언어:',
        'detected': '감지됨:',
        'install_to': '설치 위치:',
        'motionbuilder': 'MotionBuilder',
        'max': '3ds Max',
        'unreal': '언리얼 엔진',
        'install_livelink': 'Max LiveLink 설치',
        'python_path': 'Python 경로:',
        'browse': '찾아보기',
        'not_detected': '감지되지 않음',
        'ready': '설치 준비 완료',
        'exit': '종료',
        'install': '설치',
        'no_selection': '선택 없음',
        'no_selection_msg': '설치할 애플리케이션을 하나 이상 선택하세요.',
        'missing_path': '경로 누락',
        'missing_path_msg': '언리얼 엔진 Python 경로를 지정하세요.',
        'preparing': '설치 준비 중...',
        'copying': '파일 복사 중...',
        'configuring': '시작 스크립트 구성 중...',
        'finalizing': '마무리 중...',
        'installing_ue': '언리얼 엔진 지원 설치 중...',
        'complete': '설치 완료',
        'complete_msg': 'MotionKit이 성공적으로 설치되었습니다!',
        'error': '설치 오류',
        'error_msg': '설치 실패:',
        'install_complete': '설치 완료',
        'install_failed': '설치 실패',
        'dcc_apps': '개 DCC 애플리케이션',
        'ue_livelink': '언리얼 엔진 Max LiveLink'
    }
}


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
    
    def __init__(self, selected_dccs, install_ue, ue_path, translations):
        super().__init__()
        self.selected_dccs = selected_dccs
        self.install_ue = install_ue
        self.ue_path = ue_path
        self.t = translations
    
    def run(self):
        """Execute installation"""
        try:
            steps = [
                (self.t['preparing'], 20),
                (self.t['copying'], 50),
                (self.t['configuring'], 80),
                (self.t['finalizing'], 100)
            ]
            
            for msg, prog in steps:
                self.progress.emit(prog, msg)
                time.sleep(0.5)
            
            # Install UE support if requested
            if self.install_ue:
                self.progress.emit(90, self.t['installing_ue'])
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
                summary.append(f"{len(self.selected_dccs)} {self.t['dcc_apps']}")
            if self.install_ue:
                summary.append(self.t['ue_livelink'])
            
            summary_text = "\n".join(f"• {s}" for s in summary)
            self.finished.emit(True, f"{self.t['complete_msg']}\n\n{summary_text}")
            
        except Exception as e:
            self.finished.emit(False, f"{self.t['error_msg']}\n{str(e)}")


class InstallerWindow(QMainWindow):
    """Main installer window"""
    
    def __init__(self):
        super().__init__()
        
        # Current language
        self.current_lang = 'en'
        
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
    
    def t(self, key: str) -> str:
        """Get translation"""
        return TRANSLATIONS[self.current_lang].get(key, key)
    
    def change_language(self, index: int):
        """Change language"""
        langs = ['en', 'zh', 'ko']
        self.current_lang = langs[index]
        self.update_ui_text()
    
    def update_ui_text(self):
        """Update all UI text with current language"""
        self.setWindowTitle(self.t('title'))
        self.title_label.setText(self.t('title'))
        self.version_label.setText(f"{self.t('version')} {self.version}")
        self.subtitle_label.setText(self.t('subtitle'))
        self.lang_label.setText(self.t('language'))
        
        # Update group box titles
        self.mobu_detected_label.setText(self.t('detected'))
        self.mobu_install_label.setText(self.t('install_to'))
        self.mobu_group.setTitle(self.t('motionbuilder'))
        
        self.max_detected_label.setText(self.t('detected'))
        self.max_install_label.setText(self.t('install_to'))
        self.max_group.setTitle(self.t('max'))
        
        self.ue_group.setTitle(self.t('unreal'))
        self.ue_checkbox.setText(self.t('install_livelink'))
        self.ue_path_label.setText(self.t('python_path'))
        self.browse_btn.setText(self.t('browse'))
        
        # Update buttons
        self.status_label.setText(self.t('ready'))
        self.exit_btn.setText(self.t('exit'))
        self.install_btn.setText(self.t('install'))
        
        # Update "Not detected" labels
        if not self.mobu_versions:
            for i in range(self.mobu_install_layout.count()):
                widget = self.mobu_install_layout.itemAt(i).widget()
                if isinstance(widget, QLabel):
                    widget.setText(self.t('not_detected'))
        
        if not self.max_versions:
            for i in range(self.max_install_layout.count()):
                widget = self.max_install_layout.itemAt(i).widget()
                if isinstance(widget, QLabel):
                    widget.setText(self.t('not_detected'))
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle(self.t('title'))
        self.setFixedSize(700, 750)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        central.setLayout(layout)
        
        # Header with language selector
        header_layout = QHBoxLayout()
        
        # Left side - title
        title_layout = QVBoxLayout()
        self.title_label = QLabel(self.t('title'))
        self.title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_layout.addWidget(self.title_label)
        
        self.version_label = QLabel(f"{self.t('version')} {self.version}")
        self.version_label.setFont(QFont("Arial", 10))
        title_layout.addWidget(self.version_label)
        
        self.subtitle_label = QLabel(self.t('subtitle'))
        self.subtitle_label.setFont(QFont("Arial", 10))
        title_layout.addWidget(self.subtitle_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Right side - language selector
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel(self.t('language'))
        self.lang_label.setFont(QFont("Arial", 10))
        lang_layout.addWidget(self.lang_label)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['English', '中文', '한국어'])
        self.lang_combo.setFont(QFont("Arial", 10))
        self.lang_combo.setFixedWidth(120)
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        lang_layout.addWidget(self.lang_combo)
        
        header_layout.addLayout(lang_layout)
        layout.addLayout(header_layout)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # MotionBuilder section
        self.mobu_group = QGroupBox(self.t('motionbuilder'))
        self.mobu_group.setFont(QFont("Arial", 12, QFont.Bold))
        mobu_layout = QVBoxLayout()
        mobu_layout.setSpacing(8)
        
        # Detected section
        self.mobu_detected_label = QLabel(self.t('detected'))
        self.mobu_detected_label.setFont(QFont("Arial", 10, QFont.Bold))
        mobu_layout.addWidget(self.mobu_detected_label)
        
        mobu_detected_layout = QVBoxLayout()
        mobu_detected_layout.setContentsMargins(20, 0, 0, 0)
        if self.mobu_versions:
            for ver in self.mobu_versions:
                label = QLabel(f"✓ {ver['name']}")
                label.setFont(QFont("Arial", 10))
                mobu_detected_layout.addWidget(label)
        else:
            label = QLabel(self.t('not_detected'))
            label.setFont(QFont("Arial", 10))
            label.setStyleSheet("color: gray;")
            mobu_detected_layout.addWidget(label)
        mobu_layout.addLayout(mobu_detected_layout)
        
        # Install To section
        self.mobu_install_label = QLabel(self.t('install_to'))
        self.mobu_install_label.setFont(QFont("Arial", 10, QFont.Bold))
        mobu_layout.addWidget(self.mobu_install_label)
        
        self.mobu_install_layout = QVBoxLayout()
        self.mobu_install_layout.setContentsMargins(20, 0, 0, 0)
        if self.mobu_versions:
            for ver in self.mobu_versions:
                cb = QCheckBox(ver['name'])
                cb.setChecked(True)
                cb.setFont(QFont("Arial", 11))
                self.dcc_checkboxes[ver['name']] = {'checkbox': cb, 'path': ver['path']}
                self.mobu_install_layout.addWidget(cb)
        else:
            label = QLabel(self.t('not_detected'))
            label.setFont(QFont("Arial", 10))
            label.setStyleSheet("color: gray;")
            self.mobu_install_layout.addWidget(label)
        mobu_layout.addLayout(self.mobu_install_layout)
        
        self.mobu_group.setLayout(mobu_layout)
        layout.addWidget(self.mobu_group)
        
        # 3ds Max section
        self.max_group = QGroupBox(self.t('max'))
        self.max_group.setFont(QFont("Arial", 12, QFont.Bold))
        max_layout = QVBoxLayout()
        max_layout.setSpacing(8)
        
        # Detected section
        self.max_detected_label = QLabel(self.t('detected'))
        self.max_detected_label.setFont(QFont("Arial", 10, QFont.Bold))
        max_layout.addWidget(self.max_detected_label)
        
        max_detected_layout = QVBoxLayout()
        max_detected_layout.setContentsMargins(20, 0, 0, 0)
        if self.max_versions:
            for ver in self.max_versions:
                label = QLabel(f"✓ {ver['name']}")
                label.setFont(QFont("Arial", 10))
                max_detected_layout.addWidget(label)
        else:
            label = QLabel(self.t('not_detected'))
            label.setFont(QFont("Arial", 10))
            label.setStyleSheet("color: gray;")
            max_detected_layout.addWidget(label)
        max_layout.addLayout(max_detected_layout)
        
        # Install To section
        self.max_install_label = QLabel(self.t('install_to'))
        self.max_install_label.setFont(QFont("Arial", 10, QFont.Bold))
        max_layout.addWidget(self.max_install_label)
        
        self.max_install_layout = QVBoxLayout()
        self.max_install_layout.setContentsMargins(20, 0, 0, 0)
        if self.max_versions:
            for ver in self.max_versions:
                cb = QCheckBox(ver['name'])
                cb.setChecked(True)
                cb.setFont(QFont("Arial", 11))
                self.dcc_checkboxes[ver['name']] = {'checkbox': cb, 'path': ver['path']}
                self.max_install_layout.addWidget(cb)
        else:
            label = QLabel(self.t('not_detected'))
            label.setFont(QFont("Arial", 10))
            label.setStyleSheet("color: gray;")
            self.max_install_layout.addWidget(label)
        max_layout.addLayout(self.max_install_layout)
        
        self.max_group.setLayout(max_layout)
        layout.addWidget(self.max_group)
        
        # Unreal Engine section
        self.ue_group = QGroupBox(self.t('unreal'))
        self.ue_group.setFont(QFont("Arial", 12, QFont.Bold))
        ue_layout = QVBoxLayout()
        ue_layout.setSpacing(10)
        
        self.ue_checkbox = QCheckBox(self.t('install_livelink'))
        self.ue_checkbox.setFont(QFont("Arial", 11))
        ue_layout.addWidget(self.ue_checkbox)
        
        # Path selection
        path_layout = QHBoxLayout()
        self.ue_path_label = QLabel(self.t('python_path'))
        self.ue_path_label.setFont(QFont("Arial", 10))
        path_layout.addWidget(self.ue_path_label)
        
        self.ue_path_edit = QLineEdit(self.ue_path)
        self.ue_path_edit.setFont(QFont("Arial", 11))
        self.ue_path_edit.setMinimumHeight(30)
        path_layout.addWidget(self.ue_path_edit)
        
        self.browse_btn = QPushButton(self.t('browse'))
        self.browse_btn.setFont(QFont("Arial", 10))
        self.browse_btn.setMinimumHeight(30)
        self.browse_btn.setFixedWidth(100)
        self.browse_btn.clicked.connect(self.browse_ue_path)
        path_layout.addWidget(self.browse_btn)
        
        ue_layout.addLayout(path_layout)
        self.ue_group.setLayout(ue_layout)
        layout.addWidget(self.ue_group)
        
        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)
        
        # Status
        self.status_label = QLabel(self.t('ready'))
        self.status_label.setFont(QFont("Arial", 11))
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(25)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.exit_btn = QPushButton(self.t('exit'))
        self.exit_btn.setFont(QFont("Arial", 12))
        self.exit_btn.setFixedSize(150, 45)
        self.exit_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.exit_btn)
        
        btn_layout.addStretch()
        
        self.install_btn = QPushButton(self.t('install'))
        self.install_btn.setFont(QFont("Arial", 12, QFont.Bold))
        self.install_btn.setFixedSize(150, 45)
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
                self.t('no_selection'),
                self.t('no_selection_msg')
            )
            return
        
        if install_ue and not self.ue_path_edit.text():
            QMessageBox.warning(
                self,
                self.t('missing_path'),
                self.t('missing_path_msg')
            )
            return
        
        # Disable install button
        self.install_btn.setEnabled(False)
        
        # Start installation thread
        self.install_thread = InstallThread(
            selected, 
            install_ue, 
            self.ue_path_edit.text(),
            TRANSLATIONS[self.current_lang]
        )
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
            QMessageBox.information(self, self.t('complete'), message)
            self.status_label.setText(self.t('install_complete'))
        else:
            QMessageBox.critical(self, self.t('error'), message)
            self.status_label.setText(self.t('install_failed'))


def main():
    app = QApplication(sys.argv)
    window = InstallerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
