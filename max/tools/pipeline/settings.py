"""
MotionKit Settings Tool for 3ds Max
Configure Perforce connection and export paths
"""

import subprocess
import os
from pathlib import Path

try:
    import pymxs
    rt = pymxs.runtime
except ImportError:
    print("[Settings] ERROR: pymxs not available")
    pymxs = None
    rt = None

from core.config import config
from core.logger import logger
from core.localization import t

TOOL_NAME = "Settings"


def execute():
    """Execute the Settings tool"""
    if not pymxs or not rt:
        print("[Settings] ERROR: Not running in 3ds Max")
        return

    try:
        # Build the settings dialog using MaxScript
        settings_dialog = SettingsDialog()
        settings_dialog.show()

    except Exception as e:
        logger.error(f"Failed to open settings: {str(e)}")
        rt.messageBox(f"Failed to open settings:\n{str(e)}", title="MotionKit Settings Error")


class SettingsDialog:
    """Settings dialog for MotionKit in 3ds Max"""

    def __init__(self):
        self.dialog_open = False

    def show(self):
        """Show the settings dialog using MaxScript"""

        # Load current settings
        p4_server = config.get('perforce.server', '')
        p4_user = config.get('perforce.user', '')
        p4_workspace = config.get('perforce.workspace', '')
        fbx_path = config.get('export.fbx_path', '')
        current_language = config.get('ui.language', 'en')

        # Get all translations
        title = t('settings.title')
        language = t('settings.language')
        language_label = t('settings.language_label')
        perforce_group = t('settings.perforce_group')
        perforce_info = t('settings.perforce_info')
        server = t('settings.server')
        user = t('settings.user')
        workspace = t('settings.workspace')
        load_workspaces = t('settings.load_workspaces')
        test_connection = t('settings.test_connection')
        status = t('settings.status')
        status_not_connected = t('settings.status_not_connected')
        status_connected = t('settings.status_connected')
        export_group = t('settings.export_group')
        fbx_path_label = t('settings.fbx_path')
        browse = t('common.browse')
        save = t('common.save')
        save_close = t('settings.save_close')
        cancel = t('common.cancel')

        # Error messages
        error_server_user = t('settings.error_server_user')
        error_fill_all = t('settings.error_fill_all')
        p4_configured = t('settings.p4_configured')
        saved_msg = t('settings.saved')
        saved_reload_msg = t('settings.saved_reload')

        # Generate MaxScript for the dialog
        maxscript = f'''
rollout MotionKitSettingsRollout "{title}" width:520 height:300
(
    -- Language Settings Group
    group "{language}"
    (
        label lblLanguageInfo "{language_label}" pos:[20,23] width:150 align:#left
        dropdownList ddlLanguage items:#("English", "中文 (Chinese)", "한국어 (Korean)") \\
            selection:{1 if current_language == 'en' else (2 if current_language == 'zh' else 3)} \\
            pos:[175,20] width:320
    )

    -- Perforce Settings Group
    group "{perforce_group}"
    (
        label lblP4Info "{perforce_info}" pos:[20,90] width:480 align:#left

        label lblServer "{server}" pos:[20,115] width:80 align:#left
        editText edtServer "" text:"{self._escape_maxscript(p4_server)}" pos:[105,112] width:390 height:22 labelOnTop:false

        label lblUser "{user}" pos:[20,145] width:80 align:#left
        editText edtUser "" text:"{self._escape_maxscript(p4_user)}" pos:[105,142] width:390 height:22 labelOnTop:false

        label lblWorkspace "{workspace}" pos:[20,175] width:80 align:#left
        dropdownList ddlWorkspace items:#("{p4_workspace if p4_workspace else '(Not loaded)'}") selection:1 pos:[105,172] width:390

        button btnLoadWorkspaces "{load_workspaces}" pos:[20,210] width:155 height:26
        button btnTestConnection "{test_connection}" pos:[185,210] width:155 height:26

        label lblStatusDot "●" pos:[20,246] width:15 align:#left
        label lblStatus "{status} {status_not_connected}" pos:[40,246] width:455 align:#left
    )

    -- Buttons
    button btnSave "{save}" width:85 height:30 pos:[200, 262]
    button btnApplyClose "{save_close}" width:115 height:30 pos:[295, 262]
    button btnCancel "{cancel}" width:85 height:30 pos:[420, 262]

    -- Initialize status dot color (red = not connected)
    on MotionKitSettingsRollout open do
    (
        lblStatusDot.color = (color 220 60 60)
    )

    -- Event handlers
    on btnLoadWorkspaces pressed do
    (
        local server = edtServer.text
        local user = edtUser.text

        if server == "" or user == "" then
        (
            messageBox "{error_server_user}" title:"{title}"
        )
        else
        (
            python.execute ("import max.tools.pipeline.settings; max.tools.pipeline.settings._load_workspaces('" + server + "', '" + user + "')")
        )
    )

    on btnTestConnection pressed do
    (
        local server = edtServer.text
        local user = edtUser.text
        local workspace = ddlWorkspace.selected

        if server == "" or user == "" or workspace == "(Not loaded)" then
        (
            messageBox "{error_fill_all}" title:"{title}"
            lblStatusDot.color = (color 220 60 60)  -- Red
        )
        else
        (
            -- Set P4 environment variables
            python.execute ("import os; os.environ['P4PORT'] = '" + server + "'")
            python.execute ("import os; os.environ['P4USER'] = '" + user + "'")
            python.execute ("import os; os.environ['P4CLIENT'] = '" + workspace + "'")

            lblStatus.text = "{status} {status_connected}"
            lblStatusDot.color = (color 60 220 60)  -- Green
            local msg = substituteString "{p4_configured}" "{{0}}" server
            msg = substituteString msg "{{1}}" user
            msg = substituteString msg "{{2}}" workspace
            messageBox msg title:"{title}"
        )
    )

    on btnSave pressed do
    (
        local langCode = if ddlLanguage.selection == 1 then "en" else (if ddlLanguage.selection == 2 then "zh" else "ko")
        python.execute ("import max.tools.pipeline.settings; max.tools.pipeline.settings._save_settings('" + edtServer.text + "', '" + edtUser.text + "', '" + ddlWorkspace.selected + "', '" + langCode + "')")
        local langChanged = python.evaluate ("max.tools.pipeline.settings._lang_changed")
        if langChanged == true then
        (
            messageBox "{saved_reload_msg}" title:"{title}"
        )
        else
        (
            messageBox "{saved_msg}" title:"{title}"
        )
    )

    on btnApplyClose pressed do
    (
        local langCode = if ddlLanguage.selection == 1 then "en" else (if ddlLanguage.selection == 2 then "zh" else "ko")
        python.execute ("import max.tools.pipeline.settings; max.tools.pipeline.settings._save_settings('" + edtServer.text + "', '" + edtUser.text + "', '" + ddlWorkspace.selected + "', '" + langCode + "')")
        local langChanged = python.evaluate ("max.tools.pipeline.settings._lang_changed")
        if langChanged == true then
        (
            messageBox "{saved_reload_msg}" title:"{title}"
        )
        else
        (
            messageBox "{saved_msg}" title:"{title}"
        )
        destroyDialog MotionKitSettingsRollout
    )

    on btnCancel pressed do
    (
        destroyDialog MotionKitSettingsRollout
    )
)

createDialog MotionKitSettingsRollout
'''

        # Execute the MaxScript to show the dialog
        rt.execute(maxscript)

    def _escape_maxscript(self, text):
        """Escape special characters for MaxScript strings"""
        if not text:
            return ""
        # Escape backslashes and quotes
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        return text


# Global functions called from MaxScript
_current_workspaces = []
_lang_changed = False


def _load_workspaces(server, user):
    """Load Perforce workspaces (called from MaxScript)"""
    global _current_workspaces

    try:
        # Set P4 environment variables
        os.environ['P4PORT'] = server
        os.environ['P4USER'] = user

        # Run p4 clients command
        result = subprocess.run(
            ['p4', 'clients', '-u', user],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            # Parse workspace names
            workspaces = []
            for line in result.stdout.splitlines():
                if line.startswith('Client '):
                    # Format: Client workspace_name 2024/01/01 root /path 'Description'
                    parts = line.split()
                    if len(parts) >= 2:
                        workspaces.append(parts[1])

            if workspaces:
                _current_workspaces = workspaces

                # Update the dropdown in MaxScript
                workspace_array = "#(" + ", ".join([f'"{w}"' for w in workspaces]) + ")"
                rt.execute(f"MotionKitSettingsRollout.ddlWorkspace.items = {workspace_array}")
                rt.execute("MotionKitSettingsRollout.ddlWorkspace.selection = 1")
                status_msg = t('settings.status') + " " + t('settings.status_found_workspaces').format(len(workspaces))
                rt.execute(f'MotionKitSettingsRollout.lblStatus.text = "{status_msg}"')

                logger.info(f"Loaded {len(workspaces)} Perforce workspaces")
            else:
                status_msg = t('settings.status') + " " + t('settings.status_no_workspaces')
                rt.execute(f'MotionKitSettingsRollout.lblStatus.text = "{status_msg}"')
                logger.warning("No Perforce workspaces found")

        else:
            error_msg = result.stderr if result.stderr else "Unknown error"
            status_msg = t('settings.status') + " " + t('settings.status_error_loading')
            rt.execute(f'MotionKitSettingsRollout.lblStatus.text = "{status_msg}"')
            logger.error(f"Failed to load workspaces: {error_msg}")

    except FileNotFoundError:
        status_msg = t('settings.status') + " " + t('settings.status_p4_not_found')
        rt.execute(f'MotionKitSettingsRollout.lblStatus.text = "{status_msg}"')
        rt.messageBox(
            t('settings.p4_not_found_msg'),
            title=t('settings.title')
        )
        logger.error("P4 command-line tool not found")

    except subprocess.TimeoutExpired:
        status_msg = t('settings.status') + " " + t('settings.status_timeout')
        rt.execute(f'MotionKitSettingsRollout.lblStatus.text = "{status_msg}"')
        logger.error("Perforce connection timeout")

    except Exception as e:
        status_msg = t('settings.status') + f" Error - {str(e)[:30]}..."
        rt.execute(f'MotionKitSettingsRollout.lblStatus.text = "{status_msg}"')
        logger.error(f"Failed to load workspaces: {str(e)}")


def _save_settings(server, user, workspace, language='en'):
    """Save settings to config (called from MaxScript)"""
    global _lang_changed
    try:
        # Check if language changed
        current_language = config.get('ui.language', 'en')
        _lang_changed = (current_language != language)

        # Save language setting
        config.set('ui.language', language)

        # Save P4 settings
        config.set('perforce.server', server)
        config.set('perforce.user', user)

        if workspace and not workspace.startswith("("):
            config.set('perforce.workspace', workspace)
        else:
            config.set('perforce.workspace', '')

        # Save to file
        config.save()

        logger.info("Settings saved to config file")
        return True

    except Exception as e:
        rt.messageBox(
            t('settings.save_failed').format(str(e)),
            title=t('settings.title')
        )
        logger.error(f"Failed to save settings: {str(e)}")
        _lang_changed = False
        return False
