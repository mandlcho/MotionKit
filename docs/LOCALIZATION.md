# MotionKit Localization System

## Overview
MotionKit includes a comprehensive localization system supporting multiple languages for all UI elements, buttons, labels, and messages.

## Supported Languages

| Language | Code | Native Name |
|----------|------|-------------|
| English | `en` | English |
| Chinese (Simplified) | `zh` | 中文 |
| Korean | `ko` | 한국어 |

## Quick Start

### Changing Language

1. Open **MotionKit → Settings**
2. In the **Language / 语言 / 언어** section, select your preferred language
3. Click **"Save and Close"**
4. Reload MotionKit (MotionKit → Reload MotionKit)

The entire UI will now display in your selected language!

## Architecture

### File Structure

```
MotionKit/
├── core/
│   └── localization.py          # Localization system core
├── localization/
│   ├── en.json                  # English translations
│   ├── zh.json                  # Chinese translations
│   └── ko.json                  # Korean translations
└── config/
    └── config.json              # Language preference stored here
```

### How It Works

1. **Language Files**: JSON files containing all translations
2. **Localization Module**: Python module that loads and manages translations
3. **Translation Keys**: Hierarchical keys (e.g., `tools.root_anim_copy.title`)
4. **Config Storage**: User's language preference saved in config

## For Developers

### Using Localization in Python

```python
from core.localization import t, get_localization

# Get translated string
title = t('tools.root_anim_copy.title')

# With default fallback
button_text = t('common.ok', default='OK')

# Get current language
from core.localization import get_current_language
lang = get_current_language()  # Returns 'en', 'zh', or 'ko'

# Set language programmatically
from core.localization import set_language
set_language('zh')  # Switch to Chinese
```

### Using Localization in MaxScript

MaxScript tools load translations via Python and generate localized UI:

```python
from core.localization import t

# Generate MaxScript with translations
maxscript = f'''
rollout MyTool "{t('tools.my_tool.title')}"
(
    button btnOk "{t('common.ok')}" width:80
    button btnCancel "{t('common.cancel')}" width:80
)
'''
```

### Translation Key Structure

Translation keys use dot notation for hierarchical organization:

```
common.ok                           # Common UI elements
common.cancel
tools.root_anim_copy.title         # Tool-specific strings
tools.root_anim_copy.copy_button
settings.language                  # Settings dialog strings
menu.settings                      # Menu items
```

### Adding New Translations

#### 1. Add to English (`localization/en.json`)

```json
{
  "tools": {
    "my_new_tool": {
      "title": "My New Tool",
      "button_start": "Start Process",
      "error_no_selection": "Please select an object first!"
    }
  }
}
```

#### 2. Add to Chinese (`localization/zh.json`)

```json
{
  "tools": {
    "my_new_tool": {
      "title": "我的新工具",
      "button_start": "开始处理",
      "error_no_selection": "请先选择一个对象！"
    }
  }
}
```

#### 3. Add to Korean (`localization/ko.json`)

```json
{
  "tools": {
    "my_new_tool": {
      "title": "내 새 도구",
      "button_start": "프로세스 시작",
      "error_no_selection": "먼저 객체를 선택하세요!"
    }
  }
}
```

#### 4. Use in Your Tool

```python
from core.localization import t

def execute():
    title = t('tools.my_new_tool.title')
    button_text = t('tools.my_new_tool.button_start')
    error_msg = t('tools.my_new_tool.error_no_selection')
```

### String Interpolation

For strings with dynamic values, use Python's format:

```python
# In translation file:
"success_copied": "Successfully copied {0} frames!"

# In code:
from core.localization import t
frames = 120
message = t('tools.root_anim_copy.success_copied').format(frames)
# Result: "Successfully copied 120 frames!"
```

## Translation Guidelines

### General Principles

1. **Keep it concise** - UI space is limited
2. **Be consistent** - Use the same terms throughout
3. **Context matters** - Consider where text appears
4. **Test thoroughly** - Verify text fits in UI elements

### Chinese Translation Tips

- Use **Simplified Chinese** (简体中文) not Traditional
- Technical terms: Keep as English or use common Chinese equivalent
  - FBX → FBX (keep)
  - Biped → Biped (keep) or 两足系统
  - Root → 根节点
- Action buttons: Use simple verbs
  - "Copy" → "复制"
  - "Calculate" → "计算"
  - "Apply" → "应用"

### Korean Translation Tips

- Use polite/formal language (합쇼체)
- Technical terms: Often borrowed from English
  - FBX → FBX
  - Biped → Biped
  - Root → 루트
- Action buttons: Use verb + "하기" or just verb
  - "Copy" → "복사"
  - "Calculate" → "계산"
  - "Apply" → "적용"

### String Length Considerations

Different languages have different lengths for the same concept:

| English | Chinese | Korean | Max Width |
|---------|---------|--------|-----------|
| OK | 确定 | 확인 | Short |
| Calculate from Selection | 从选择计算 | 선택에서 계산 | Long |
| Settings | 设置 | 설정 | Short |

Design UI with **longest expected translation** in mind.

## Common Translation Keys

### Common UI Elements

```json
{
  "common": {
    "ok": "OK / 确定 / 확인",
    "cancel": "Cancel / 取消 / 취소",
    "save": "Save / 保存 / 저장",
    "close": "Close / 关闭 / 닫기",
    "apply": "Apply / 应用 / 적용",
    "browse": "Browse... / 浏览... / 찾아보기...",
    "pick": "Pick / 拾取 / 선택",
    "calculate": "Calculate / 计算 / 계산"
  }
}
```

### Menu Items

```json
{
  "menu": {
    "settings": "Settings... / 设置... / 설정...",
    "reload": "Reload MotionKit / 重新加载 / 다시 로드",
    "about": "About MotionKit / 关于 / 정보"
  }
}
```

## API Reference

### `core.localization` Module

#### Functions

**`t(key, default=None)`**
- Get translated string for current language
- Args:
  - `key` (str): Translation key
  - `default` (str, optional): Fallback text
- Returns: Translated string

**`get_localization()`**
- Get global localization instance
- Returns: Localization object

**`set_language(lang_code)`**
- Set current language
- Args: `lang_code` ('en', 'zh', 'ko')
- Returns: True if successful

**`get_current_language()`**
- Get current language code
- Returns: 'en', 'zh', or 'ko'

#### Localization Class

**`Localization()`**
- Main localization manager

**Methods:**
- `get(key, default)` - Get translation
- `set_language(lang_code)` - Change language
- `get_language_name(lang_code)` - Get language display name
- `get_available_languages()` - Get all supported languages

## Testing Translations

### Manual Testing

1. Switch to each language in Settings
2. Open each tool
3. Verify:
   - ✓ All text is translated
   - ✓ Text fits in UI elements
   - ✓ No truncation or overflow
   - ✓ Buttons are clickable
   - ✓ Error messages display correctly

### Automated Testing

```python
# Test all keys exist in all languages
from core.localization import get_localization

loc = get_localization()

# Check a key in all languages
for lang in ['en', 'zh', 'ko']:
    loc.set_language(lang)
    text = loc.get('common.ok')
    print(f"{lang}: {text}")
```

## Troubleshooting

### Issue: Text Not Translated

**Cause**: Translation key missing or incorrect
**Solution**: Check key exists in all language files

### Issue: Language Not Changing

**Cause**: MotionKit not reloaded after language change
**Solution**: MotionKit → Reload MotionKit

### Issue: Text Overflows UI

**Cause**: Translation longer than UI element width
**Solution**: Use shorter translation or increase UI element width

### Issue: Chinese/Korean Characters Not Displaying

**Cause**: Font doesn't support characters
**Solution**: 3ds Max should support these by default. Check system fonts.

## Future Enhancements

Potential improvements for localization system:

- [ ] Add Japanese (日本語) support
- [ ] Add French support
- [ ] Runtime language switching (no reload required)
- [ ] Translation validation tool
- [ ] Pluralization support
- [ ] Right-to-left language support (Arabic, Hebrew)
- [ ] Translation memory system

## Contributing Translations

To contribute translations:

1. Fork the repository
2. Add/update translations in `localization/*.json`
3. Test thoroughly with actual tools
4. Submit pull request with:
   - Language file changes
   - Screenshots showing translated UI
   - Description of what was translated

## Support

For localization issues or questions:
- GitHub Issues: https://github.com/mandlcho/MotionKit/issues
- Label your issue with `localization` tag
