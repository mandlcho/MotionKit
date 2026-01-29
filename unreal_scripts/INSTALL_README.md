# Max LiveLink Installation - SUPER SIMPLE

## 🚀 Method 1: Auto-Install on Every UE Launch (EASIEST)

**One-time setup (30 seconds):**

1. Copy `init_unreal.py` to:
   ```
   C:\Users\elementa\Documents\UnrealEngine\Python\init_unreal.py
   ```

2. Restart Unreal Engine

3. **Done!** Max LiveLink menu appears automatically in every project

---

## 📋 Method 2: One-Line Paste (Quick & Manual)

1. Open Unreal Engine
2. Open Output Log: `Window → Developer Tools → Output Log`
3. Click the `Python` tab
4. Paste this single line:
   ```python
   exec(open(r"C:\Users\elementa\projects\MotionKit\unreal_scripts\install_max_livelink.py").read())
   ```
5. Press Enter
6. **Done!** Menu persists even after restarting UE

---

## 🎯 Method 3: Execute Script (Traditional)

1. Open Unreal Engine
2. Go to `Tools → Execute Python Script`
3. Browse to `install_max_livelink.py`
4. Click Execute
5. **Done!**

---

## ✅ After Installation

You'll see: **Tools → Max LiveLink** with these options:
- ▶ **Start Max LiveLink Server** - Click to start
- ■ **Stop Max LiveLink Server** - Click to stop  
- 🔧 **Test Connection** - Check if running

---

## 💡 Which Method Should I Use?

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **Method 1** | Everyone | Zero-click auto-install | One-time file copy |
| **Method 2** | Quick testing | Fast, one line | Manual each project |
| **Method 3** | Traditional users | Familiar workflow | Most clicks |

**Recommendation: Use Method 1** - Copy `init_unreal.py` once, never think about it again!

---

## 🔧 Troubleshooting

**Menu doesn't appear?**
- Check Output Log for errors
- Make sure Python plugin is enabled in UE: `Edit → Plugins → Python Editor Script Plugin`

**init_unreal.py not working?**
- Verify path: `C:\Users\elementa\Documents\UnrealEngine\Python\init_unreal.py`
- Check file permissions (not read-only)
- Restart Unreal Engine completely

**Need to uninstall?**
- Delete or rename `init_unreal.py` from the Python folder
- Restart UE
