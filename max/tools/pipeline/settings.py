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

        # Generate MaxScript for the dialog
        maxscript = f'''
rollout MotionKitSettingsRollout "MotionKit Settings" width:480 height:340
(
    -- Perforce Settings Group
    group "Perforce Settings"
    (
        label lblP4Info "Configure your Perforce connection:" align:#left

        label lblServer "Server:" align:#left across:2
        editText edtServer "" text:"{self._escape_maxscript(p4_server)}" fieldWidth:350 align:#right

        label lblUser "User:" align:#left across:2
        editText edtUser "" text:"{self._escape_maxscript(p4_user)}" fieldWidth:350 align:#right

        label lblWorkspace "Workspace:" align:#left across:2
        dropdownList ddlWorkspace items:#("(Not loaded)") selection:1 width:350 align:#right

        button btnLoadWorkspaces "Load Workspaces" width:150 height:24 align:#left
        button btnTestConnection "Test Connection" width:150 height:24 align:#left offset:[160, -28]

        label lblStatus "Status: Not connected" align:#left
    )

    -- Export Settings Group
    group "Export Settings"
    (
        label lblExport "FBX Export Path:" align:#left across:2
        editText edtFbxPath "" text:"{self._escape_maxscript(fbx_path)}" fieldWidth:300 align:#right
        button btnBrowse "Browse..." width:70 height:20 align:#right offset:[0, -22]
    )

    -- Buttons
    button btnSave "Save" width:80 height:28 pos:[180, 300]
    button btnApplyClose "Save and Close" width:110 height:28 pos:[270, 300]
    button btnCancel "Cancel" width:80 height:28 pos:[390, 300]

    -- Event handlers
    on btnLoadWorkspaces pressed do
    (
        local server = edtServer.text
        local user = edtUser.text

        if server == "" or user == "" then
        (
            messageBox "Please enter Server and User first" title:"MotionKit Settings"
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
            messageBox "Please fill in Server, User, and load Workspaces first" title:"MotionKit Settings"
        )
        else
        (
            -- Set P4 environment variables
            python.execute ("import os; os.environ['P4PORT'] = '" + server + "'")
            python.execute ("import os; os.environ['P4USER'] = '" + user + "'")
            python.execute ("import os; os.environ['P4CLIENT'] = '" + workspace + "'")

            lblStatus.text = "Status: Connection configured"
            messageBox ("Perforce settings configured:\\n\\nServer: " + server + "\\nUser: " + user + "\\nWorkspace: " + workspace + "\\n\\nEnvironment variables have been set.") title:"MotionKit Settings"
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
        python.execute ("import max.tools.pipeline.settings; max.tools.pipeline.settings._save_settings('" + edtServer.text + "', '" + edtUser.text + "', '" + ddlWorkspace.selected + "', '" + edtFbxPath.text + "')")
        messageBox "Settings saved successfully!" title:"MotionKit Settings"
    )

    on btnApplyClose pressed do
    (
        python.execute ("import max.tools.pipeline.settings; max.tools.pipeline.settings._save_settings('" + edtServer.text + "', '" + edtUser.text + "', '" + ddlWorkspace.selected + "', '" + edtFbxPath.text + "')")
        messageBox "Settings saved successfully!" title:"MotionKit Settings"
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
                rt.execute(f'MotionKitSettingsRollout.lblStatus.text = "Status: Found {len(workspaces)} workspace(s)"')

                logger.info(f"Loaded {len(workspaces)} Perforce workspaces")
            else:
                rt.execute('MotionKitSettingsRollout.lblStatus.text = "Status: No workspaces found"')
                logger.warning("No Perforce workspaces found")

        else:
            error_msg = result.stderr if result.stderr else "Unknown error"
            rt.execute(f'MotionKitSettingsRollout.lblStatus.text = "Status: Error loading workspaces"')
            logger.error(f"Failed to load workspaces: {error_msg}")

    except FileNotFoundError:
        rt.execute('MotionKitSettingsRollout.lblStatus.text = "Status: P4 CLI not found"')
        rt.messageBox(
            "Perforce command-line tool (p4) not found.\\n\\nPlease install P4 CLI and ensure it's in your PATH.",
            title="MotionKit Settings"
        )
        logger.error("P4 command-line tool not found")

    except subprocess.TimeoutExpired:
        rt.execute('MotionKitSettingsRollout.lblStatus.text = "Status: Connection timeout"')
        logger.error("Perforce connection timeout")

    except Exception as e:
        rt.execute(f'MotionKitSettingsRollout.lblStatus.text = "Status: Error - {str(e)[:30]}..."')
        logger.error(f"Failed to load workspaces: {str(e)}")


def _save_settings(server, user, workspace, fbx_path):
    """Save settings to config (called from MaxScript)"""
    try:
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
                    f"The path does not exist:\n{fbx_path}\n\nCreate it?",
                    title="MotionKit Settings"
                )
                if result:
                    try:
                        path_obj.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        rt.messageBox(
                            f"Failed to create directory:\n{str(e)}",
                            title="MotionKit Settings Error"
                        )
                        return False

        config.set('export.fbx_path', fbx_path)

        # Save to file
        config.save()

        logger.info("Settings saved to config file")
        return True

    except Exception as e:
        rt.messageBox(
            f"Failed to save settings:\n{str(e)}",
            title="MotionKit Settings Error"
        )
        logger.error(f"Failed to save settings: {str(e)}")
        return False
