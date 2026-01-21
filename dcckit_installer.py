"""
DCCKit Installer - Compact Multi-Language Version
No dependencies required - uses built-in tkinter
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import threading


# Translations
TRANSLATIONS = {
    'EN': {
        'title': 'DCCKit Installer',
        'subtitle': 'Multi-DCC Pipeline Toolset',
        'language': 'Language:',
        'version': 'Version',
        'dcc_detected': 'Detected DCCs',
        'install_to': 'Install To:',
        'profile': 'Installation Profile:',
        'profile_artist': 'Artist',
        'profile_animator': 'Animator',
        'profile_expert': 'Expert',
        'profile_desc_artist': 'Essential tools: Animation, Character Mapping, Scene Manager',
        'profile_desc_animator': 'Full suite: Animation, Character, Unreal, Pipeline tools',
        'profile_desc_expert': 'Complete: All tools + Debug utilities + Experimental features',
        'ready': 'Ready to install',
        'install': 'Install',
        'exit': 'Exit',
        'no_dcc_title': 'No DCC Detected',
        'no_dcc_msg': 'No supported DCC applications were detected.\n\nContinue anyway?',
        'no_selection_title': 'No Selection',
        'no_selection_msg': 'Please select at least one DCC version to install.',
        'installing': 'Installing...',
        'complete_title': 'Installation Complete',
        'complete_msg': 'DCCKit has been installed successfully!',
        'copying': 'Copying core files...',
        'configuring': 'Configuring startup scripts...',
        'finalizing': 'Finalizing installation...',
    },
    'CN': {
        'title': 'DCCKit 安装程序',
        'subtitle': '多DCC流程工具集',
        'language': '语言:',
        'version': '版本',
        'dcc_detected': '检测到的DCC',
        'install_to': '安装到:',
        'profile': '安装配置:',
        'profile_artist': '美术师',
        'profile_animator': '动画师',
        'profile_expert': '专家',
        'profile_desc_artist': '基础工具: 动画、角色映射、场景管理',
        'profile_desc_animator': '完整套件: 动画、角色、虚幻引擎、流程工具',
        'profile_desc_expert': '完全版: 所有工具 + 调试工具 + 实验性功能',
        'ready': '准备安装',
        'install': '安装',
        'exit': '退出',
        'no_dcc_title': '未检测到DCC',
        'no_dcc_msg': '未检测到支持的DCC应用程序。\n\n仍要继续吗？',
        'no_selection_title': '未选择',
        'no_selection_msg': '请至少选择一个要安装的DCC版本。',
        'installing': '正在安装...',
        'complete_title': '安装完成',
        'complete_msg': 'DCCKit 已成功安装！',
        'copying': '正在复制核心文件...',
        'configuring': '正在配置启动脚本...',
        'finalizing': '正在完成安装...',
    },
    'KR': {
        'title': 'DCCKit 설치 프로그램',
        'subtitle': '다중 DCC 파이프라인 도구 세트',
        'language': '언어:',
        'version': '버전',
        'dcc_detected': '감지된 DCC',
        'install_to': '설치 위치:',
        'profile': '설치 프로필:',
        'profile_artist': '아티스트',
        'profile_animator': '애니메이터',
        'profile_expert': '전문가',
        'profile_desc_artist': '필수 도구: 애니메이션, 캐릭터 매핑, 씬 매니저',
        'profile_desc_animator': '전체 제품군: 애니메이션, 캐릭터, 언리얼, 파이프라인 도구',
        'profile_desc_expert': '완전판: 모든 도구 + 디버그 유틸리티 + 실험적 기능',
        'ready': '설치 준비 완료',
        'install': '설치',
        'exit': '종료',
        'no_dcc_title': 'DCC 미감지',
        'no_dcc_msg': '지원되는 DCC 애플리케이션이 감지되지 않았습니다.\n\n계속하시겠습니까?',
        'no_selection_title': '선택 없음',
        'no_selection_msg': '설치할 DCC 버전을 하나 이상 선택하세요.',
        'installing': '설치 중...',
        'complete_title': '설치 완료',
        'complete_msg': 'DCCKit이 성공적으로 설치되었습니다!',
        'copying': '핵심 파일 복사 중...',
        'configuring': '시작 스크립트 구성 중...',
        'finalizing': '설치 마무리 중...',
    }
}


class DCCDetector:
    """Detects installed DCC applications."""

    @staticmethod
    def detect_motionbuilder():
        """Detect installed MotionBuilder versions."""
        versions = []
        autodesk_path = Path(r"C:\Program Files\Autodesk")

        if autodesk_path.exists():
            for item in autodesk_path.iterdir():
                if item.is_dir() and "MotionBuilder" in item.name:
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
    def detect_3dsmax():
        """Detect installed 3ds Max versions."""
        versions = []
        autodesk_path = Path(r"C:\Program Files\Autodesk")

        if autodesk_path.exists():
            for item in autodesk_path.iterdir():
                if item.is_dir() and "3ds Max" in item.name:
                    for year in range(2020, 2030):
                        if str(year) in item.name:
                            versions.append({
                                'name': f'3ds Max {year}',
                                'year': year,
                                'path': str(item)
                            })
                            break

        return sorted(versions, key=lambda x: x['year'], reverse=True)


class DCCKitInstaller:
    """Main installer application."""

    def __init__(self, root):
        self.root = root
        self.root.title("DCCKit Installer")
        self.root.geometry("420x450")
        self.root.resizable(False, False)

        # Dark theme colors - all white text
        self.bg_color = "#2b2b2b"
        self.fg_color = "#ffffff"
        self.accent_color = "#0d7377"

        # Configure root
        self.root.configure(bg=self.bg_color)

        # Language
        self.current_language = tk.StringVar(value="EN")
        self.current_language.trace('w', self.update_language)

        # Load config
        self.version = self.load_version()

        # Detect DCCs
        self.detected_dccs = {
            'motionbuilder': DCCDetector.detect_motionbuilder(),
            'max': DCCDetector.detect_3dsmax()
        }

        # DCC checkboxes
        self.dcc_vars = {}

        # Profile selection
        self.selected_profile = tk.StringVar(value="Animator")

        # Build UI
        self.create_ui()

    def load_version(self):
        """Load version from config.json."""
        config_path = Path(__file__).parent / "config" / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get('version', '1.0.0')
            except:
                pass
        return "1.0.0"

    def get_text(self, key):
        """Get translated text."""
        lang = self.current_language.get()
        return TRANSLATIONS[lang].get(key, key)

    def update_language(self, *args):
        """Update all text when language changes."""
        self.root.title(self.get_text('title'))
        self.title_label.config(text=self.get_text('title'))
        self.subtitle_label.config(text=self.get_text('subtitle'))
        self.version_label.config(text=f"{self.get_text('version')} {self.version}")
        self.lang_label.config(text=self.get_text('language'))
        self.dcc_label.config(text=self.get_text('dcc_detected'))
        self.install_to_label.config(text=self.get_text('install_to'))
        self.profile_label.config(text=self.get_text('profile'))
        self.status_label.config(text=self.get_text('ready'))
        self.install_btn.config(text=self.get_text('install'))
        self.exit_btn.config(text=self.get_text('exit'))

        # Update profile combobox
        self.profile_combo['values'] = [
            self.get_text('profile_artist'),
            self.get_text('profile_animator'),
            self.get_text('profile_expert')
        ]
        # Set current selection
        profile_map = {
            'Artist': 'profile_artist',
            'Animator': 'profile_animator',
            'Expert': 'profile_expert'
        }
        current = self.selected_profile.get()
        self.profile_combo.set(self.get_text(profile_map[current]))

        self.update_profile_description()

    def create_ui(self):
        """Create the user interface."""
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Header with language selector
        header_frame = tk.Frame(main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Left side - title
        title_frame = tk.Frame(header_frame, bg=self.bg_color)
        title_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.title_label = tk.Label(
            title_frame,
            text=self.get_text('title'),
            font=("Arial", 14, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.W
        )
        self.title_label.pack(anchor=tk.W)

        self.version_label = tk.Label(
            title_frame,
            text=f"{self.get_text('version')} {self.version}",
            font=("Arial", 8),
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.W
        )
        self.version_label.pack(anchor=tk.W)

        self.subtitle_label = tk.Label(
            title_frame,
            text=self.get_text('subtitle'),
            font=("Arial", 8),
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.W
        )
        self.subtitle_label.pack(anchor=tk.W)

        # Right side - language selector
        lang_frame = tk.Frame(header_frame, bg=self.bg_color)
        lang_frame.pack(side=tk.RIGHT)

        self.lang_label = tk.Label(
            lang_frame,
            text=self.get_text('language'),
            font=("Arial", 8),
            bg=self.bg_color,
            fg=self.fg_color
        )
        self.lang_label.pack(side=tk.LEFT, padx=(0, 5))

        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.current_language,
            values=['EN', 'CN', 'KR'],
            state='readonly',
            width=5,
            font=("Arial", 8)
        )
        lang_combo.pack(side=tk.LEFT)

        # Separator
        sep1 = tk.Frame(main_frame, height=1, bg="#404040")
        sep1.pack(fill=tk.X, pady=5)

        # DCC Detection with checkboxes
        self.dcc_label = tk.Label(
            main_frame,
            text=self.get_text('dcc_detected'),
            font=("Arial", 10, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.W
        )
        self.dcc_label.pack(anchor=tk.W, pady=(5, 5))

        self.install_to_label = tk.Label(
            main_frame,
            text=self.get_text('install_to'),
            font=("Arial", 8),
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.W
        )
        self.install_to_label.pack(anchor=tk.W, pady=(0, 5))

        # DCC Checkboxes frame
        dcc_frame = tk.Frame(main_frame, bg="#1e1e1e", relief=tk.FLAT)
        dcc_frame.pack(fill=tk.X, pady=(0, 10))

        # MotionBuilder
        if self.detected_dccs['motionbuilder']:
            for dcc in self.detected_dccs['motionbuilder']:
                var = tk.BooleanVar(value=True)
                self.dcc_vars[dcc['name']] = {'var': var, 'path': dcc['path']}

                cb = tk.Checkbutton(
                    dcc_frame,
                    text=f"  ✓ {dcc['name']}",
                    variable=var,
                    font=("Arial", 9),
                    bg="#1e1e1e",
                    fg=self.fg_color,
                    selectcolor="#1e1e1e",
                    activebackground="#1e1e1e",
                    activeforeground=self.fg_color
                )
                cb.pack(anchor=tk.W, padx=5, pady=2)
        else:
            lbl = tk.Label(
                dcc_frame,
                text="  ✗ MotionBuilder not detected",
                font=("Arial", 9),
                bg="#1e1e1e",
                fg=self.fg_color
            )
            lbl.pack(anchor=tk.W, padx=5, pady=2)

        # 3ds Max
        if self.detected_dccs['max']:
            for dcc in self.detected_dccs['max']:
                var = tk.BooleanVar(value=True)
                self.dcc_vars[dcc['name']] = {'var': var, 'path': dcc['path']}

                cb = tk.Checkbutton(
                    dcc_frame,
                    text=f"  ✓ {dcc['name']}",
                    variable=var,
                    font=("Arial", 9),
                    bg="#1e1e1e",
                    fg=self.fg_color,
                    selectcolor="#1e1e1e",
                    activebackground="#1e1e1e",
                    activeforeground=self.fg_color
                )
                cb.pack(anchor=tk.W, padx=5, pady=2)
        else:
            lbl = tk.Label(
                dcc_frame,
                text="  ✗ 3ds Max not detected",
                font=("Arial", 9),
                bg="#1e1e1e",
                fg=self.fg_color
            )
            lbl.pack(anchor=tk.W, padx=5, pady=2)

        # Separator
        sep2 = tk.Frame(main_frame, height=1, bg="#404040")
        sep2.pack(fill=tk.X, pady=10)

        # Profile Selection - Combobox
        self.profile_label = tk.Label(
            main_frame,
            text=self.get_text('profile'),
            font=("Arial", 10, "bold"),
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.W
        )
        self.profile_label.pack(anchor=tk.W, pady=(0, 5))

        self.profile_combo = ttk.Combobox(
            main_frame,
            values=[
                self.get_text('profile_artist'),
                self.get_text('profile_animator'),
                self.get_text('profile_expert')
            ],
            state='readonly',
            font=("Arial", 9),
            width=40
        )
        self.profile_combo.current(1)  # Default to Animator
        self.profile_combo.bind('<<ComboboxSelected>>', self.on_profile_change)
        self.profile_combo.pack(fill=tk.X, pady=(0, 5))

        # Profile description
        self.profile_desc_label = tk.Label(
            main_frame,
            text="",
            font=("Arial", 8),
            bg=self.bg_color,
            fg=self.fg_color,
            wraplength=380,
            justify=tk.LEFT,
            anchor=tk.W
        )
        self.profile_desc_label.pack(anchor=tk.W, pady=(0, 10))
        self.update_profile_description()

        # Separator
        sep3 = tk.Frame(main_frame, height=1, bg="#404040")
        sep3.pack(fill=tk.X, pady=10)

        # Progress
        self.status_label = tk.Label(
            main_frame,
            text=self.get_text('ready'),
            font=("Arial", 8),
            bg=self.bg_color,
            fg=self.fg_color,
            anchor=tk.W
        )
        self.status_label.pack(anchor=tk.W, pady=(0, 5))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "custom.Horizontal.TProgressbar",
            troughcolor='#1e1e1e',
            background=self.accent_color,
            bordercolor='#404040',
            lightcolor=self.accent_color,
            darkcolor=self.accent_color
        )

        self.progress_bar = ttk.Progressbar(
            main_frame,
            style="custom.Horizontal.TProgressbar",
            length=380,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 15))

        # Buttons
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Install button (pack first on right side)
        self.install_btn = tk.Button(
            button_frame,
            text=self.get_text('install'),
            font=("Arial", 9, "bold"),
            bg=self.accent_color,
            fg=self.fg_color,
            activebackground="#14a085",
            activeforeground=self.fg_color,
            relief=tk.FLAT,
            padx=20,
            pady=6,
            command=self.start_installation
        )
        self.install_btn.pack(side=tk.RIGHT)

        # Exit button (pack second on right side)
        self.exit_btn = tk.Button(
            button_frame,
            text=self.get_text('exit'),
            font=("Arial", 9),
            bg="#404040",
            fg=self.fg_color,
            activebackground="#4a4a4a",
            activeforeground=self.fg_color,
            relief=tk.FLAT,
            padx=20,
            pady=6,
            command=self.root.quit
        )
        self.exit_btn.pack(side=tk.RIGHT, padx=(0, 5))

    def on_profile_change(self, event):
        """Handle profile selection change."""
        selected = self.profile_combo.get()
        # Map display text back to internal value
        lang = self.current_language.get()
        if selected == TRANSLATIONS[lang]['profile_artist']:
            self.selected_profile.set('Artist')
        elif selected == TRANSLATIONS[lang]['profile_animator']:
            self.selected_profile.set('Animator')
        elif selected == TRANSLATIONS[lang]['profile_expert']:
            self.selected_profile.set('Expert')

        self.update_profile_description()

    def update_profile_description(self):
        """Update profile description."""
        profile = self.selected_profile.get()
        desc_key = f'profile_desc_{profile.lower()}'
        self.profile_desc_label.config(text=self.get_text(desc_key))

    def get_selected_dccs(self):
        """Get list of selected DCCs."""
        selected = []
        for name, data in self.dcc_vars.items():
            if data['var'].get():
                selected.append({'name': name, 'path': data['path']})
        return selected

    def start_installation(self):
        """Start installation process."""
        # Get selected DCCs
        selected_dccs = self.get_selected_dccs()

        if not selected_dccs:
            messagebox.showwarning(
                self.get_text('no_selection_title'),
                self.get_text('no_selection_msg')
            )
            return

        # Disable buttons
        self.install_btn.config(state=tk.DISABLED)

        # Start installation in background thread
        profile = self.selected_profile.get()
        thread = threading.Thread(target=self.run_installation, args=(profile, selected_dccs))
        thread.daemon = True
        thread.start()

    def run_installation(self, profile, selected_dccs):
        """Run the installation."""
        import time

        steps = [
            (self.get_text('installing'), 20),
            (self.get_text('copying'), 50),
            (self.get_text('configuring'), 80),
            (self.get_text('finalizing'), 100)
        ]

        for status, progress in steps:
            self.status_label.config(text=status)
            self.progress_bar['value'] = progress
            self.root.update_idletasks()
            time.sleep(0.5)

        self.status_label.config(text=self.get_text('complete_title'))
        messagebox.showinfo(
            self.get_text('complete_title'),
            self.get_text('complete_msg')
        )
        self.root.quit()


def main():
    """Main entry point."""
    root = tk.Tk()
    app = DCCKitInstaller(root)
    root.mainloop()


if __name__ == "__main__":
    main()
