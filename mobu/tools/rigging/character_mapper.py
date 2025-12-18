"""
Character Mapper Tool
Visual character mapping with preset save/load functionality
"""

from pyfbsdk import (
    FBCharacter, FBBodyNodeId, FBSystem, FBMessageBox,
    FBFilePopup, FBFilePopupStyle
)
from PySide2 import QtWidgets, QtCore

from core.logger import logger
from core.qt import load_ui, show_tool_window
from pathlib import Path
import json
import shutil

TOOL_NAME = "Character Mapper"

# Character bone slots in logical order
CHARACTER_SLOTS = [
    ("Reference", "Reference"),
    ("Hips", "Hips"),
    ("Spine", "Spine"),
    ("Spine1", "Spine1"),
    ("Spine2", "Spine2"),
    ("Spine3", "Spine3"),
    ("Spine4", "Spine4"),
    ("Spine5", "Spine5"),
    ("Spine6", "Spine6"),
    ("Spine7", "Spine7"),
    ("Spine8", "Spine8"),
    ("Spine9", "Spine9"),
    ("Neck", "Neck"),
    ("Head", "Head"),
    ("LeftShoulder", "LeftShoulder"),
    ("LeftArm", "LeftArm"),
    ("LeftForeArm", "LeftForeArm"),
    ("LeftHand", "LeftHand"),
    ("RightShoulder", "RightShoulder"),
    ("RightArm", "RightArm"),
    ("RightForeArm", "RightForeArm"),
    ("RightHand", "RightHand"),
    ("LeftUpLeg", "LeftUpLeg"),
    ("LeftLeg", "LeftLeg"),
    ("LeftFoot", "LeftFoot"),
    ("RightUpLeg", "RightUpLeg"),
    ("RightLeg", "RightLeg"),
    ("RightFoot", "RightFoot"),
]


class CharacterMapperUI(QtWidgets.QWidget):
    """Visual character mapping tool with preset management"""

    def __init__(self, parent=None):
        super(CharacterMapperUI, self).__init__(parent)
        
        # Load the UI file
        ui_path = Path(__file__).parent / "character_mapper.ui"
        self.ui = load_ui(ui_path, self)

        # Attach the UI to the widget's layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.ui)
        self.setLayout(layout)

        self.setWindowTitle(TOOL_NAME)

        self.character = None
        self.bone_mappings = {}  # slot_name -> model_name
        self.preset_path = self._get_preset_path()

        self._connect_signals()
        self.populate_mapping_list()
        self.LoadSceneModels()

    def _get_preset_path(self):
        """Get the path to the presets directory"""
        root = Path(__file__).parent.parent.parent.parent
        preset_dir = root / "presets" / "characters"
        preset_dir.mkdir(parents=True, exist_ok=True)
        return preset_dir

    def _connect_signals(self):
        """Connect UI widget signals to methods"""
        self.ui.assign_btn.clicked.connect(self.OnAssignBone)
        self.ui.refresh_btn.clicked.connect(self.LoadSceneModels)
        self.ui.characterize_btn.clicked.connect(self.OnCharacterize)
        self.ui.clear_btn.clicked.connect(self.OnClearMapping)
        self.ui.save_btn.clicked.connect(self.OnSavePreset)
        self.ui.load_btn.clicked.connect(self.OnLoadPreset)
        self.ui.export_btn.clicked.connect(self.OnExportPreset)
        self.ui.import_btn.clicked.connect(self.OnImportPreset)

    def populate_mapping_list(self):
        """Populate the mapping list with character slots"""
        self.ui.mapping_list.clear()
        for slot_name, _ in CHARACTER_SLOTS:
            self.bone_mappings[slot_name] = None
            self.ui.mapping_list.addItem(f"{slot_name}: <None>")

    def LoadSceneModels(self):
        """Load all scene models into the objects list"""
        self.ui.objects_list.clear()
        scene = FBSystem().Scene
        for model in scene.RootModel.Children:
            self._add_model_recursive(model)

    def _add_model_recursive(self, model):
        """Recursively add models to the list"""
        self.ui.objects_list.addItem(model.LongName)
        for child in model.Children:
            self._add_model_recursive(child)

    def OnAssignBone(self):
        """Assign selected object to selected bone slot"""
        mapping_item = self.ui.mapping_list.currentItem()
        object_item = self.ui.objects_list.currentItem()

        if not mapping_item:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a bone slot first.")
            return

        if not object_item:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a scene object.")
            return
        
        slot_index = self.ui.mapping_list.row(mapping_item)
        slot_name = CHARACTER_SLOTS[slot_index][0]
        object_name = object_item.text()

        self.bone_mappings[slot_name] = object_name
        mapping_item.setText(f"{slot_name}: {object_name}")

        logger.info(f"Mapped {slot_name} -> {object_name}")

    def OnClearMapping(self):
        """Clear all bone mappings"""
        self.populate_mapping_list()
        logger.info("Cleared all mappings")

    def OnCharacterize(self):
        """Create character from current mapping"""
        logger.info("Creating character...")

        try:
            required = ["Hips", "LeftUpLeg", "RightUpLeg", "Spine"]
            missing = [slot for slot in required if not self.bone_mappings.get(slot)]

            if missing:
                QtWidgets.QMessageBox.warning(
                    self, "Missing Required Bones",
                    f"Please map these required bones:\n{', '.join(missing)}"
                )
                return

            preset_name = self.ui.preset_name_edit.text() or "Character"
            self.character = FBCharacter(preset_name)

            for slot_name, _ in CHARACTER_SLOTS:
                bone_name = self.bone_mappings.get(slot_name)
                if bone_name:
                    model = FBSystem().Scene.FindModelByLabelName(bone_name)
                    if model:
                        prop = self.character.PropertyList.Find(f"{slot_name}Link")
                        if prop:
                            prop.append(model)
                            logger.info(f"Linked {slot_name} -> {model.Name}")

            if not self.character.Characterize():
                error_msg = "Characterization failed. Check bone positions and hierarchy."
                QtWidgets.QMessageBox.critical(self, "Characterization Error", error_msg)
                logger.error(error_msg)
            else:
                QtWidgets.QMessageBox.information(
                    self, "Success",
                    f"Character '{self.character.Name}' created successfully!"
                )
                logger.info(f"Character created: {self.character.Name}")

        except Exception as e:
            logger.error(f"Characterization failed: {str(e)}", exc_info=True)
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create character:\n{str(e)}")

    def OnSavePreset(self):
        """Save current mapping as a preset"""
        preset_name = self.ui.preset_name_edit.text()
        if not preset_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a preset name.")
            return

        preset_data = {
            "name": preset_name,
            "version": "1.0",
            "mappings": {k: v for k, v in self.bone_mappings.items() if v}
        }

        preset_file = self.preset_path / f"{preset_name}.json"
        try:
            with open(preset_file, 'w') as f:
                json.dump(preset_data, f, indent=2)
            QtWidgets.QMessageBox.information(self, "Preset Saved", f"Preset saved to:\n{preset_file}")
            logger.info(f"Saved preset: {preset_file}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save preset:\n{str(e)}")
            logger.error(f"Failed to save preset: {str(e)}")

    def OnLoadPreset(self):
        """Load a preset from the internal presets folder"""
        preset_name = self.ui.preset_name_edit.text()
        if not preset_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a preset name to load.")
            return
            
        preset_file = self.preset_path / f"{preset_name}.json"
        self._load_preset_file(preset_file)

    def OnExportPreset(self):
        """Export preset to an external file"""
        preset_name = self.ui.preset_name_edit.text()
        if not preset_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please enter a preset name to export.")
            return

        preset_file = self.preset_path / f"{preset_name}.json"
        if not preset_file.exists():
            QtWidgets.QMessageBox.warning(self, "Preset Not Found", f"Preset '{preset_name}' not found. Please save it first.")
            return

        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Character Preset", str(self.preset_path), "JSON Files (*.json)")
        if save_path:
            try:
                shutil.copy2(preset_file, save_path)
                QtWidgets.QMessageBox.information(self, "Export Successful", f"Preset exported to:\n{save_path}")
                logger.info(f"Exported preset to: {save_path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to export preset:\n{str(e)}")
                logger.error(f"Failed to export preset: {str(e)}")

    def OnImportPreset(self):
        """Import preset from an external file"""
        open_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Import Character Preset", str(self.preset_path), "JSON Files (*.json)")
        if open_path:
            self._load_preset_file(Path(open_path))

    def _load_preset_file(self, preset_file):
        """Helper to load and apply a preset file"""
        if not preset_file.exists():
            QtWidgets.QMessageBox.warning(self, "Preset Not Found", f"Preset not found at:\n{preset_file}")
            return

        try:
            with open(preset_file, 'r') as f:
                preset_data = json.load(f)

            self.OnClearMapping()
            
            preset_name = preset_data.get("name", preset_file.stem)
            self.ui.preset_name_edit.setText(preset_name)

            for slot_name, bone_name in preset_data.get("mappings", {}).items():
                if slot_name in self.bone_mappings:
                    self.bone_mappings[slot_name] = bone_name
            
            self._update_mapping_list_display()

            QtWidgets.QMessageBox.information(self, "Preset Loaded", f"Preset '{preset_name}' loaded successfully!")
            logger.info(f"Loaded preset: {preset_file}")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load preset:\n{str(e)}")
            logger.error(f"Failed to load preset: {str(e)}")

    def _update_mapping_list_display(self):
        """Update the UI list from the internal bone_mappings dict"""
        self.ui.mapping_list.clear()
        for slot_name, _ in CHARACTER_SLOTS:
            bone_name = self.bone_mappings.get(slot_name, "<None>") or "<None>"
            self.ui.mapping_list.addItem(f"{slot_name}: {bone_name}")


def execute(control, event):
    """Show the Character Mapper tool"""
    show_tool_window(CharacterMapperUI, name=TOOL_NAME)
