"""
xMobu Settings Tool
Configure P4 connection and export paths
"""

from pyfbsdk import (
    FBTool, FBLayout, FBButton, FBLabel, FBEdit, FBList,
    FBAttachType, FBMessageBox, FBAddRegionParam, ShowTool,
    FBTextStyle, FBListStyle, FBFilePopup, FBFilePopupStyle,
    FBSystem, FBEditProperty
)
from core.decorators import CreateUniqueTool
from core.config import config
from core.logger import logger
from pathlib import Path

TOOL_NAME = "xMobu Settings"


def execute(control, event):
    """Execute the Settings tool"""
    tool = SettingsUI()
    tool.StartSizeX = 600
    tool.StartSizeY = 500
    return tool


@CreateUniqueTool
class SettingsUI(FBTool):
    """Settings management tool for xMobu"""

    def __init__(self):
        FBTool.__init__(self, "SettingsUI")
        self.workspaces = []  # Store available workspaces
        self.BuildUI()
        self.LoadSettings()
        print("[Settings] Tool initialized")

    def BuildUI(self):
        """Build the tool interface"""
        # Main regions
        x = FBAddRegionParam(0, FBAttachType.kFBAttachLeft, "")
        y = FBAddRegionParam(0, FBAttachType.kFBAttachTop, "")
        w = FBAddRegionParam(0, FBAttachType.kFBAttachRight, "")
        h = FBAddRegionParam(0, FBAttachType.kFBAttachBottom, "")

        # Create main layout
        main = FBLayout()
        self.AddRegion("main", "main", x, y, w, h)
        self.SetControl("main", main)

        # Split into sections
        y_top = FBAddRegionParam(0, FBAttachType.kFBAttachTop, "")
        y_mid = FBAddRegionParam(-150, FBAttachType.kFBAttachBottom, "")
        y_bottom = FBAddRegionParam(0, FBAttachType.kFBAttachBottom, "")

        # Top panel - Settings
        settings_layout = FBLayout()
        main.AddRegion("settings", "settings", x, y_top, w, y_mid)
        main.SetControl("settings", settings_layout)

        # Bottom panel - Actions
        actions_layout = FBLayout()
        main.AddRegion("actions", "actions", x, y_mid, w, y_bottom)
        main.SetControl("actions", actions_layout)

        # Build sub-panels
        self._build_settings_panel(settings_layout)
        self._build_actions_panel(actions_layout)

    def _build_settings_panel(self, layout):
        """Build the settings panel"""
        x = FBAddRegionParam(10, FBAttachType.kFBAttachLeft, "")
        w = FBAddRegionParam(-10, FBAttachType.kFBAttachRight, "")

        y_offset = 10
        row_height = 25
        spacing = 5

        # Title
        title = FBLabel()
        title.Caption = "xMobu Settings"
        title.Style = FBTextStyle.kFBTextStyleBold

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + row_height, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("title", "title", x, y1, w, y2)
        layout.SetControl("title", title)
        y_offset += row_height + spacing * 2

        # === Perforce Settings ===
        p4_header = FBLabel()
        p4_header.Caption = "Perforce Version Control"
        p4_header.Style = FBTextStyle.kFBTextStyleBold

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + row_height, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("p4_header", "p4_header", x, y1, w, y2)
        layout.SetControl("p4_header", p4_header)
        y_offset += row_height + spacing

        # P4 Server
        p4_server_label = FBLabel()
        p4_server_label.Caption = "Server:"

        x_label = FBAddRegionParam(10, FBAttachType.kFBAttachLeft, "")
        x_field = FBAddRegionParam(100, FBAttachType.kFBAttachLeft, "")
        w_field = FBAddRegionParam(-10, FBAttachType.kFBAttachRight, "")

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + row_height, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("p4_server_label", "p4_server_label", x_label, y1, x_field, y2)
        layout.SetControl("p4_server_label", p4_server_label)

        self.p4_server_edit = FBEdit()
        self.p4_server_edit.Text = ""
        self.p4_server_edit.OnChange.Add(self.OnP4CredentialsChanged)
        layout.AddRegion("p4_server", "p4_server", x_field, y1, w_field, y2)
        layout.SetControl("p4_server", self.p4_server_edit)
        y_offset += row_height + spacing

        # P4 User
        p4_user_label = FBLabel()
        p4_user_label.Caption = "User:"

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + row_height, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("p4_user_label", "p4_user_label", x_label, y1, x_field, y2)
        layout.SetControl("p4_user_label", p4_user_label)

        self.p4_user_edit = FBEdit()
        self.p4_user_edit.Text = ""
        self.p4_user_edit.OnChange.Add(self.OnP4CredentialsChanged)
        layout.AddRegion("p4_user", "p4_user", x_field, y1, w_field, y2)
        layout.SetControl("p4_user", self.p4_user_edit)
        y_offset += row_height + spacing

        # P4 Workspace (dropdown list)
        p4_workspace_label = FBLabel()
        p4_workspace_label.Caption = "Workspace:"

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + 80, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("p4_workspace_label", "p4_workspace_label", x_label, y1, x_field, y2)
        layout.SetControl("p4_workspace_label", p4_workspace_label)

        self.p4_workspace_list = FBList()
        self.p4_workspace_list.Style = FBListStyle.kFBVerticalList
        self.p4_workspace_list.MultiSelect = False
        layout.AddRegion("p4_workspace", "p4_workspace", x_field, y1, w_field, y2)
        layout.SetControl("p4_workspace", self.p4_workspace_list)
        y_offset += 85

        # P4 Connection Status
        self.p4_status_label = FBLabel()
        self.p4_status_label.Caption = "Status: Not connected"

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + row_height, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("p4_status", "p4_status", x, y1, w, y2)
        layout.SetControl("p4_status", self.p4_status_label)
        y_offset += row_height + spacing

        # Test P4 Connection button
        test_p4_btn = FBButton()
        test_p4_btn.Caption = "Test Connection"
        test_p4_btn.OnClick.Add(self.OnTestP4Connection)

        x_btn = FBAddRegionParam(10, FBAttachType.kFBAttachLeft, "")
        w_btn = FBAddRegionParam(150, FBAttachType.kFBAttachLeft, "")

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + 30, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("test_p4_btn", "test_p4_btn", x_btn, y1, w_btn, y2)
        layout.SetControl("test_p4_btn", test_p4_btn)
        y_offset += 40

        # === Export Settings ===
        export_header = FBLabel()
        export_header.Caption = "Export Settings"
        export_header.Style = FBTextStyle.kFBTextStyleBold

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + row_height, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("export_header", "export_header", x, y1, w, y2)
        layout.SetControl("export_header", export_header)
        y_offset += row_height + spacing

        # FBX Export Path
        fbx_path_label = FBLabel()
        fbx_path_label.Caption = "FBX Export Path:"

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + row_height, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("fbx_path_label", "fbx_path_label", x_label, y1, x_field, y2)
        layout.SetControl("fbx_path_label", fbx_path_label)

        self.fbx_path_edit = FBEdit()
        self.fbx_path_edit.Text = ""

        x_path = FBAddRegionParam(100, FBAttachType.kFBAttachLeft, "")
        w_path = FBAddRegionParam(-100, FBAttachType.kFBAttachRight, "")
        layout.AddRegion("fbx_path", "fbx_path", x_path, y1, w_path, y2)
        layout.SetControl("fbx_path", self.fbx_path_edit)
        y_offset += row_height + spacing

        # Browse button
        browse_btn = FBButton()
        browse_btn.Caption = "Browse..."
        browse_btn.OnClick.Add(self.OnBrowseFBXPath)

        x_browse = FBAddRegionParam(-90, FBAttachType.kFBAttachRight, "")
        w_browse = FBAddRegionParam(-10, FBAttachType.kFBAttachRight, "")

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + 30, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("browse_btn", "browse_btn", x_browse, y1, w_browse, y2)
        layout.SetControl("browse_btn", browse_btn)

    def _build_actions_panel(self, layout):
        """Build the actions panel"""
        x = FBAddRegionParam(10, FBAttachType.kFBAttachLeft, "")
        w = FBAddRegionParam(-10, FBAttachType.kFBAttachRight, "")

        y_offset = 10
        button_height = 35
        spacing = 10

        # Info label
        info_label = FBLabel()
        info_label.Caption = "Click 'Save' to apply settings"

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + 20, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("info", "info", x, y1, w, y2)
        layout.SetControl("info", info_label)
        y_offset += 30

        # Save button
        save_btn = FBButton()
        save_btn.Caption = "Save Settings"
        save_btn.OnClick.Add(self.OnSaveSettings)

        x_btn1 = FBAddRegionParam(10, FBAttachType.kFBAttachLeft, "")
        x_btn2 = FBAddRegionParam(0, FBAttachType.kFBAttachNone, "")
        x_btn3 = FBAddRegionParam(-10, FBAttachType.kFBAttachRight, "")

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + button_height, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("save_btn", "save_btn", x_btn1, y1, x_btn2, y2)
        layout.SetControl("save_btn", save_btn)

        # Reset button
        reset_btn = FBButton()
        reset_btn.Caption = "Reset to Defaults"
        reset_btn.OnClick.Add(self.OnResetSettings)

        layout.AddRegion("reset_btn", "reset_btn", x_btn2, y1, x_btn3, y2)
        layout.SetControl("reset_btn", reset_btn)
        y_offset += button_height + spacing

        # Apply and Close button
        close_btn = FBButton()
        close_btn.Caption = "Apply and Close"
        close_btn.OnClick.Add(self.OnApplyAndClose)

        y1 = FBAddRegionParam(y_offset, FBAttachType.kFBAttachTop, "")
        y2 = FBAddRegionParam(y_offset + button_height, FBAttachType.kFBAttachTop, "")
        layout.AddRegion("close_btn", "close_btn", x, y1, w, y2)
        layout.SetControl("close_btn", close_btn)

    def LoadSettings(self):
        """Load settings from config"""
        # Load P4 settings
        self.p4_server_edit.Text = config.get('perforce.server', '')
        self.p4_user_edit.Text = config.get('perforce.user', '')

        saved_workspace = config.get('perforce.workspace', '')

        # Load export settings
        self.fbx_path_edit.Text = config.get('export.fbx_path', '')

        # Try to load workspaces if server and user are set
        if self.p4_server_edit.Text and self.p4_user_edit.Text:
            self.LoadWorkspaces()
            # Select the saved workspace if it exists in the list
            if saved_workspace:
                for i in range(len(self.p4_workspace_list.Items)):
                    if saved_workspace in self.p4_workspace_list.Items[i]:
                        self.p4_workspace_list.ItemIndex = i
                        break

        print("[Settings] Loaded settings from config")

    def OnP4CredentialsChanged(self, control, event):
        """Called when server or user fields change - load workspaces"""
        server = self.p4_server_edit.Text
        user = self.p4_user_edit.Text

        # Only load workspaces if both server and user are filled
        if server and user:
            print(f"[Settings] P4 credentials changed, loading workspaces...")
            self.LoadWorkspaces()

    def LoadWorkspaces(self):
        """Query P4 for available workspaces"""
        server = self.p4_server_edit.Text
        user = self.p4_user_edit.Text

        if not server or not user:
            return

        # Clear existing workspace list
        while len(self.p4_workspace_list.Items) > 0:
            self.p4_workspace_list.Items.removeAt(0)

        print(f"[Settings] Querying workspaces for {user}@{server}...")
        self.p4_status_label.Caption = "Status: Loading workspaces..."

        try:
            import subprocess
            import os

            # Set P4 environment
            env = os.environ.copy()
            env['P4PORT'] = server
            env['P4USER'] = user

            # Query P4 for workspaces
            # Using 'p4 clients -u <user>' to get workspaces for this user
            result = subprocess.run(
                ['p4', '-p', server, '-u', user, 'clients', '-u', user],
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )

            if result.returncode == 0:
                # Parse output - each line is like: "Client <workspace> <date> root <path> '<description>'"
                workspaces = []
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('Client '):
                        parts = line.split()
                        if len(parts) >= 2:
                            workspace_name = parts[1]
                            workspaces.append(workspace_name)

                if workspaces:
                    self.workspaces = workspaces
                    for ws in workspaces:
                        self.p4_workspace_list.Items.append(ws)

                    self.p4_status_label.Caption = f"Status: Found {len(workspaces)} workspace(s)"
                    print(f"[Settings] Found {len(workspaces)} workspaces: {', '.join(workspaces)}")
                else:
                    self.p4_workspace_list.Items.append("(No workspaces found)")
                    self.p4_status_label.Caption = "Status: No workspaces found"
                    print("[Settings] No workspaces found for this user")

            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.p4_workspace_list.Items.append("(Error loading workspaces)")
                self.p4_status_label.Caption = f"Status: Error - {error_msg[:30]}..."
                print(f"[Settings] P4 error: {error_msg}")
                logger.error(f"P4 query failed: {error_msg}")

        except FileNotFoundError:
            self.p4_workspace_list.Items.append("(P4 command not found)")
            self.p4_status_label.Caption = "Status: P4 CLI not installed"
            print("[Settings] P4 command-line tool not found in PATH")
            FBMessageBox(
                "P4 Not Found",
                "Perforce command-line tool (p4) not found.\n\n"
                "Please install P4 CLI and ensure it's in your PATH.\n"
                "You can manually enter your workspace name.",
                "OK"
            )

        except subprocess.TimeoutExpired:
            self.p4_workspace_list.Items.append("(Connection timeout)")
            self.p4_status_label.Caption = "Status: Connection timeout"
            print("[Settings] P4 query timed out")

        except Exception as e:
            self.p4_workspace_list.Items.append("(Error loading workspaces)")
            self.p4_status_label.Caption = f"Status: Error - {str(e)[:30]}..."
            print(f"[Settings] Error loading workspaces: {str(e)}")
            logger.error(f"Failed to load workspaces: {str(e)}")

    def OnTestP4Connection(self, control, event):
        """Test Perforce connection using MotionBuilder's version control API"""
        print("[Settings] Testing P4 connection...")

        server = self.p4_server_edit.Text
        user = self.p4_user_edit.Text

        # Get selected workspace from list
        workspace = ""
        if self.p4_workspace_list.ItemIndex >= 0:
            workspace = self.p4_workspace_list.Items[self.p4_workspace_list.ItemIndex]

        if not server or not user or not workspace or workspace.startswith("("):
            FBMessageBox(
                "Missing Information",
                "Please fill in Server, User, and Workspace fields",
                "OK"
            )
            self.p4_status_label.Caption = "Status: Missing configuration"
            return

        try:
            # Try to access MotionBuilder's version control system
            from pyfbsdk import FBVersionControl

            vc = FBVersionControl()

            # Set P4 environment variables
            import os
            os.environ['P4PORT'] = server
            os.environ['P4USER'] = user
            os.environ['P4CLIENT'] = workspace

            # Try to initialize connection
            if vc:
                # Check if we can query the connection
                # Note: MotionBuilder's P4 integration might be limited
                self.p4_status_label.Caption = "Status: Connection configured"
                FBMessageBox(
                    "P4 Configuration",
                    f"Perforce settings configured:\n\n"
                    f"Server: {server}\n"
                    f"User: {user}\n"
                    f"Workspace: {workspace}\n\n"
                    f"Note: Full P4 connection testing requires P4 command-line tools.\n"
                    f"Environment variables have been set.",
                    "OK"
                )
                print("[Settings] P4 configuration set successfully")
            else:
                self.p4_status_label.Caption = "Status: Version control not available"
                FBMessageBox(
                    "Warning",
                    "MotionBuilder version control system not available.\n"
                    "Settings will be saved for external P4 tools.",
                    "OK"
                )

        except ImportError:
            # FBVersionControl might not be available in all MB versions
            self.p4_status_label.Caption = "Status: Settings configured (MB API unavailable)"
            FBMessageBox(
                "P4 Settings",
                f"Perforce settings configured:\n\n"
                f"Server: {server}\n"
                f"User: {user}\n"
                f"Workspace: {workspace}\n\n"
                f"Note: MotionBuilder's version control API is not available.\n"
                f"Settings will be saved for external P4 integration.",
                "OK"
            )
            print("[Settings] P4 settings configured (FBVersionControl not available)")

        except Exception as e:
            self.p4_status_label.Caption = f"Status: Error - {str(e)}"
            FBMessageBox(
                "Connection Error",
                f"Failed to test P4 connection:\n{str(e)}\n\n"
                f"Check your settings and P4 installation.",
                "OK"
            )
            logger.error(f"P4 connection test failed: {str(e)}")

    def OnBrowseFBXPath(self, control, event):
        """Browse for FBX export directory"""
        popup = FBFilePopup()
        popup.Caption = "Select FBX Export Directory"
        popup.Style = FBFilePopupStyle.kFBFilePopupOpen
        popup.Path = self.fbx_path_edit.Text or ""

        # Note: FBFilePopup doesn't have a folder-only mode in all MB versions
        # So we'll let users select a file and use its parent directory
        if popup.Execute():
            selected_path = Path(popup.FullFilename)
            # Use parent directory if a file was selected
            if selected_path.is_file():
                selected_path = selected_path.parent

            self.fbx_path_edit.Text = str(selected_path)
            print(f"[Settings] FBX export path set to: {selected_path}")

    def OnSaveSettings(self, control, event):
        """Save settings to config"""
        try:
            # Save P4 settings
            config.set('perforce.server', self.p4_server_edit.Text)
            config.set('perforce.user', self.p4_user_edit.Text)

            # Get selected workspace from list
            workspace = ""
            if self.p4_workspace_list.ItemIndex >= 0:
                workspace = self.p4_workspace_list.Items[self.p4_workspace_list.ItemIndex]
                # Don't save error messages
                if workspace.startswith("("):
                    workspace = ""

            config.set('perforce.workspace', workspace)

            # Save export settings
            fbx_path = self.fbx_path_edit.Text
            if fbx_path:
                # Validate path
                path_obj = Path(fbx_path)
                if not path_obj.exists():
                    result = FBMessageBox(
                        "Path Not Found",
                        f"The path does not exist:\n{fbx_path}\n\n"
                        f"Create it or choose a different path?",
                        "Create", "Cancel"
                    )
                    if result == 1:  # Create
                        try:
                            path_obj.mkdir(parents=True, exist_ok=True)
                        except Exception as e:
                            FBMessageBox("Error", f"Failed to create directory:\n{str(e)}", "OK")
                            return
                    else:
                        return

            config.set('export.fbx_path', fbx_path)

            # Save to file
            config.save()

            FBMessageBox("Success", "Settings saved successfully!", "OK")
            print("[Settings] Settings saved to config file")

        except Exception as e:
            FBMessageBox("Error", f"Failed to save settings:\n{str(e)}", "OK")
            logger.error(f"Failed to save settings: {str(e)}")

    def OnResetSettings(self, control, event):
        """Reset settings to defaults"""
        result = FBMessageBox(
            "Reset Settings",
            "Reset all settings to default values?",
            "Yes", "No"
        )

        if result == 1:  # Yes
            self.p4_server_edit.Text = ""
            self.p4_user_edit.Text = ""

            # Clear workspace list
            while len(self.p4_workspace_list.Items) > 0:
                self.p4_workspace_list.Items.removeAt(0)

            self.fbx_path_edit.Text = ""
            self.p4_status_label.Caption = "Status: Not connected"
            print("[Settings] Settings reset to defaults")

    def OnApplyAndClose(self, control, event):
        """Save settings and close the tool"""
        self.OnSaveSettings(None, None)
        # Note: Closing the tool window programmatically is limited in MotionBuilder
        # The user will need to close it manually
        print("[Settings] Settings applied. Close window manually if needed.")
