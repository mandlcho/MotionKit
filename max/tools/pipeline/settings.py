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
rollout MotionKitSettingsRollout "{title}" width:480 height:390
(
    -- Language Settings Group
    group "{language}"
    (
        label lblLanguageInfo "{language_label}" align:#left across:2
        dropdownList ddlLanguage items:#("English", "中文 (Chinese)", "한국어 (Korean)") \\
            selection:{1 if current_language == 'en' else (2 if current_language == 'zh' else 3)} \\
            width:250 align:#right
    )

    -- Perforce Settings Group
    group "{perforce_group}"
    (
        label lblP4Info "{perforce_info}" align:#left

        label lblServer "{server}" align:#left across:2
        editText edtServer "" text:"{self._escape_maxscript(p4_server)}" fieldWidth:350 align:#right labelOnTop:false

        label lblUser "{user}" align:#left across:2
        editText edtUser "" text:"{self._escape_maxscript(p4_user)}" fieldWidth:350 align:#right labelOnTop:false

        label lblWorkspace "{workspace}" align:#left across:2
        dropdownList ddlWorkspace items:#("(Not loaded)") selection:1 width:350 align:#right

        button btnLoadWorkspaces "{load_workspaces}" width:150 height:24 align:#left
        button btnTestConnection "{test_connection}" width:150 height:24 align:#left offset:[160, -28]

        label lblStatus "{status} {status_not_connected}" align:#left
    )

    -- Export Settings Group
    group "{export_group}"
    (
        label lblExport "{fbx_path_label}" align:#left across:3
        editText edtFbxPath "" text:"{self._escape_maxscript(fbx_path)}" fieldWidth:320 align:#left labelOnTop:false
        button btnBrowse "..." width:30 height:20 align:#right
    )

    -- Buttons
    button btnSave "{save}" width:80 height:28 pos:[180, 300]
    button btnApplyClose "{save_close}" width:110 height:28 pos:[270, 300]
    button btnCancel "{cancel}" width:80 height:28 pos:[390, 300]

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
        )
        else
        (
            -- Set P4 environment variables
            python.execute ("import os; os.environ['P4PORT'] = '" + server + "'")
            python.execute ("import os; os.environ['P4USER'] = '" + user + "'")
            python.execute ("import os; os.environ['P4CLIENT'] = '" + workspace + "'")

            lblStatus.text = "{status} {status_connected}"
            local msg = substituteString "{p4_configured}" "{{0}}" server
            msg = substituteString msg "{{1}}" user
            msg = substituteString msg "{{2}}" workspace
            messageBox msg title:"{title}"
        )
    )

    on btnBrowse pressed do
    (
        local newPath = getSavePath caption:"Select FBX Export Directory"
        if newPath != undefined then
        (
            edtFbxPath.text = newPath
        )
    )

    on btnSave pressed do
    (
        local langCode = if ddlLanguage.selection == 1 then "en" else (if ddlLanguage.selection == 2 then "zh" else "ko")
        python.execute ("import max.tools.pipeline.settings; max.tools.pipeline.settings._save_settings('" + edtServer.text + "', '" + edtUser.text + "', '" + ddlWorkspace.selected + "', '" + edtFbxPath.text + "', '" + langCode + "')")
        messageBox "{saved_msg}" title:"{title}"
    )

    on btnApplyClose pressed do
    (
        local langCode = if ddlLanguage.selection == 1 then "en" else (if ddlLanguage.selection == 2 then "zh" else "ko")
        python.execute ("import max.tools.pipeline.settings; max.tools.pipeline.settings._save_settings('" + edtServer.text + "', '" + edtUser.text + "', '" + ddlWorkspace.selected + "', '" + edtFbxPath.text + "', '" + langCode + "')")
        messageBox "{saved_reload_msg}" title:"{title}"
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


def _save_settings(server, user, workspace, fbx_path, language='en'):
    """Save settings to config (called from MaxScript)"""
    try:
        # Save language setting
        config.set('ui.language', language)

        # Save P4 settings
        config.set('perforce.server', server)
        config.set('perforce.user', user)

        if workspace and not workspace.startswith("("):
            config.set('perforce.workspace', workspace)
        else:
            config.set('perforce.workspace', '')

        # Save export settings
        if fbx_path:
            path_obj = Path(fbx_path)
            if not path_obj.exists():
                # Ask if user wants to create it
                result = rt.queryBox(
                    t('settings.create_path_prompt').format(fbx_path),
                    title=t('settings.title')
                )
                if result:
                    try:
                        path_obj.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        rt.messageBox(
                            t('settings.create_path_failed').format(str(e)),
                            title=t('settings.title')
                        )
                        return False

        config.set('export.fbx_path', fbx_path)

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
        return False
