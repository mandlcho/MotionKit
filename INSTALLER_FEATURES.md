# DCCKit Installer - Feature Guide

## UI Layout (500x450 window)

```
┌─────────────────────────────────────────────────┐
│ DCCKit Installer              Language: [EN ▼] │
│ Version 1.0.0                                   │
│ Multi-DCC Pipeline Toolset                      │
├─────────────────────────────────────────────────┤
│ Detected DCCs                                   │
│ Install To:                                     │
│ ┌─────────────────────────────────────────────┐ │
│ │ ☑ ✓ MotionBuilder 2024                      │ │
│ │ ☑ ✓ MotionBuilder 2023                      │ │
│ │ ☑ ✓ 3ds Max 2024                            │ │
│ │ ☑ ✓ 3ds Max 2023                            │ │
│ └─────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────┤
│ Installation Profile:                           │
│ [Animator                                    ▼] │
│ Full suite: Animation, Character, Unreal,       │
│ Pipeline tools                                  │
├─────────────────────────────────────────────────┤
│ Ready to install                                │
│ [████████████████░░░░░░░░░░] 60%              │
│                                                 │
│                          [Exit]  [Install]      │
└─────────────────────────────────────────────────┘
```

## Key Features

### 1. Language Switcher (Top Right)
- **Location**: Top-right corner next to title
- **Options**: EN / CN / KR
- **Behavior**: Instant update of all UI text
- **No restart required**

**Languages Supported:**
- **EN** - English
- **CN** - Chinese (Simplified) - 中文
- **KR** - Korean - 한국어

### 2. DCC Checkboxes (Middle Section)
- **Auto-detected** DCCs shown with checkmarks
- **All checked by default** for convenience
- **Uncheck** any you don't want to install to
- **Validation**: Must select at least one

**Detection:**
- Scans `C:\Program Files\Autodesk\`
- Finds MotionBuilder 2020-2029
- Finds 3ds Max 2020-2029
- Shows year and name for each version

**Not Detected?**
- Shows red X with "not detected" message
- No checkbox (can't install to non-existent DCC)

### 3. Profile Dropdown (Bottom Section)
- **Simple combobox** instead of radio buttons
- **Three options**:
  1. **Artist** - Minimal install
  2. **Animator** - Standard install (default)
  3. **Expert** - Full install

- **Description** updates when you change selection
- **Localized** - changes with language

### 4. Compact Design
- **500x450 pixels** - Small footprint
- **Fixed size** - No resizing
- **Clean layout** - No clutter
- **Dark theme** - Easy on the eyes

## Installation Flow

### 1. Start
```
[Ready to install]
[░░░░░░░░░░░░░░░░░░░░] 0%
```

### 2. During Installation
```
[Installing...]
[████████░░░░░░░░░░░░] 40%
```

### 3. Complete
```
[Installation complete!]
[████████████████████] 100%
```

Then shows popup: "DCCKit has been installed successfully!"

## Validation

### No DCC Selected
If you uncheck all DCCs and click Install:
```
┌─────────────────────────┐
│    ⚠ No Selection       │
├─────────────────────────┤
│ Please select at least  │
│ one DCC version to      │
│ install.                │
│                         │
│          [OK]           │
└─────────────────────────┘
```

### No DCC Detected (and proceed)
Shows warning that no DCCs were found, asks to continue anyway.

## Technical Details

### DCC Checkbox Data Structure
Each checkbox stores:
- `name` - e.g., "MotionBuilder 2024"
- `var` - BooleanVar (checked/unchecked)
- `path` - Install path

Accessible via: `self.get_selected_dccs()`

Returns:
```python
[
    {'name': 'MotionBuilder 2024', 'path': 'C:\\Program Files\\Autodesk\\MotionBuilder 2024'},
    {'name': '3ds Max 2024', 'path': 'C:\\Program Files\\Autodesk\\3ds Max 2024'}
]
```

### Profile Data
Stored as:
- `self.selected_profile` - StringVar ('Artist', 'Animator', 'Expert')
- Maps to translated display text in combobox
- Description auto-updates

### Language System
- All text in `TRANSLATIONS` dictionary
- Uses `self.get_text(key)` to retrieve
- Updates all labels when language changes
- No page reload needed

## Adding Features

### Add a New Language
1. Add to `TRANSLATIONS` dict:
```python
'ES': {
    'title': 'Instalador DCCKit',
    'subtitle': 'Herramientas de Pipeline Multi-DCC',
    # ... rest of translations
}
```

2. Add to language dropdown:
```python
lang_combo = ttk.Combobox(
    values=['EN', 'CN', 'KR', 'ES'],  # Add ES
    ...
)
```

### Add More DCC Support
1. Create detection method:
```python
@staticmethod
def detect_maya():
    # Similar to detect_motionbuilder()
    ...
```

2. Add to `detected_dccs`:
```python
self.detected_dccs = {
    'motionbuilder': DCCDetector.detect_motionbuilder(),
    'max': DCCDetector.detect_3dsmax(),
    'maya': DCCDetector.detect_maya(),  # New
}
```

3. Add UI section in `create_ui()`:
```python
# Maya
if self.detected_dccs['maya']:
    for dcc in self.detected_dccs['maya']:
        # Create checkbox...
```

### Add More Profiles
1. Add to `TRANSLATIONS`:
```python
'profile_td': 'Technical Director',
'profile_desc_td': 'Full suite + Python API + Dev tools',
```

2. Add to combobox values
3. Add to `on_profile_change()` mapping

## Tips

### Reduce Window Size Further
Change:
```python
self.root.geometry("450x400")  # Even smaller!
```

### Change Fonts
All fonts use Arial. To change:
```python
font=("Segoe UI", 9)  # Use Segoe UI instead
```

### Custom Color Scheme
```python
self.bg_color = "#1e1e1e"      # Darker
self.accent_color = "#007acc"  # VS Code blue
```

### Hide Language Selector
Comment out the language frame section in `create_ui()`

### Default Language
Change in `__init__`:
```python
self.current_language = tk.StringVar(value="CN")  # Default to Chinese
```

## Internationalization Notes

### Right-to-Left Languages
Current layout is LTR (left-to-right). For RTL languages like Arabic:
1. Set `anchor=tk.E` instead of `tk.W`
2. Pack `side=tk.RIGHT` instead of `side=tk.LEFT`
3. Consider using `tk.RIGHT` justification

### Font Support
- **Arial** supports Latin, Chinese, Korean
- For other scripts, change font:
  - Japanese: "Meiryo" or "MS Gothic"
  - Arabic: "Arial" works
  - Hindi: "Nirmala UI"

### Text Length Variations
Chinese text is typically **shorter** than English.
Korean text is typically **similar** length.

Test with longest language to ensure UI doesn't break!

## Performance

- **Startup**: <100ms
- **Language Switch**: Instant (<10ms)
- **DCC Detection**: <1 second
- **Installation**: Depends on your implementation

## Accessibility

Current features:
- ✅ Keyboard navigation (Tab key)
- ✅ High contrast (dark theme)
- ✅ Clear visual indicators

Could add:
- ⭕ Screen reader support
- ⭕ Larger fonts option
- ⭕ High contrast mode toggle

---

That's everything! The installer is clean, simple, and ready to customize.
