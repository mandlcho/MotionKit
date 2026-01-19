"""
Localization system for MotionKit
Supports English, Chinese (Simplified), and Korean
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional


class Localization:
    """Handles localization for MotionKit UI"""

    # Supported languages
    LANGUAGES = {
        'en': 'English',
        'zh': '中文 (Chinese)',
        'ko': '한국어 (Korean)'
    }

    def __init__(self):
        self.current_language = 'en'
        self.translations: Dict[str, Dict[str, str]] = {}
        self.localization_dir = Path(__file__).parent.parent / 'localization'
        self._load_translations()
        self._load_user_preference()

    def _load_translations(self):
        """Load all translation files"""
        if not self.localization_dir.exists():
            self.localization_dir.mkdir(parents=True, exist_ok=True)

        for lang_code in self.LANGUAGES.keys():
            lang_file = self.localization_dir / f'{lang_code}.json'
            if lang_file.exists():
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    print(f"[Localization] Error loading {lang_code}.json: {e}")
                    self.translations[lang_code] = {}
            else:
                self.translations[lang_code] = {}

    def _load_user_preference(self):
        """Load user's language preference from config"""
        try:
            from core.config import config
            self.current_language = config.get('ui.language', 'en')
        except:
            self.current_language = 'en'

    def set_language(self, lang_code: str) -> bool:
        """
        Set the current language

        Args:
            lang_code: Language code (en, zh, ko)

        Returns:
            True if successful, False otherwise
        """
        if lang_code not in self.LANGUAGES:
            print(f"[Localization] Unsupported language: {lang_code}")
            return False

        self.current_language = lang_code

        # Save to config
        try:
            from core.config import config
            config.set('ui.language', lang_code)
            config.save()
        except Exception as e:
            print(f"[Localization] Error saving language preference: {e}")

        return True

    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Get translated string for the current language

        Args:
            key: Translation key (e.g., 'common.ok', 'tools.root_anim_copy.title')
            default: Default text if translation not found

        Returns:
            Translated string or default or key
        """
        if self.current_language not in self.translations:
            return default or key

        # Support nested keys with dot notation
        keys = key.split('.')
        value = self.translations[self.current_language]

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default or key

        return value if isinstance(value, str) else (default or key)

    def get_language_name(self, lang_code: Optional[str] = None) -> str:
        """Get the display name of a language"""
        code = lang_code or self.current_language
        return self.LANGUAGES.get(code, 'Unknown')

    def get_available_languages(self) -> Dict[str, str]:
        """Get all available languages"""
        return self.LANGUAGES.copy()


# Global localization instance
_localization = None


def get_localization() -> Localization:
    """Get the global localization instance"""
    global _localization
    if _localization is None:
        _localization = Localization()
    return _localization


def t(key: str, default: Optional[str] = None) -> str:
    """
    Shorthand function to get translated string

    Args:
        key: Translation key
        default: Default text if not found

    Returns:
        Translated string
    """
    return get_localization().get(key, default)


def set_language(lang_code: str) -> bool:
    """
    Set the current language

    Args:
        lang_code: Language code (en, zh, ko)

    Returns:
        True if successful
    """
    return get_localization().set_language(lang_code)


def get_current_language() -> str:
    """Get the current language code"""
    return get_localization().current_language
