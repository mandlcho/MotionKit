"""
Auto-Characterization Tool
Automatically detects skeleton bones, applies T-pose, and characterizes the character
"""

from pathlib import Path

try:
    from PySide2 import QtWidgets, QtCore
    from PySide2.QtWidgets import QDialog, QMessageBox, QApplication
    from PySide2.QtCore import Qt
except ImportError:
    try:
        from PySide import QtGui as QtWidgets
        from PySide import QtCore
        from PySide.QtGui import QDialog, QMessageBox, QApplication
        from PySide.QtCore import Qt
    except ImportError:
        print("[Auto Characterize] ERROR: Neither PySide2 nor PySide found")
        QtWidgets = None

from pyfbsdk import (
    FBMessageBox, FBSystem, FBCharacter, FBVector3d, FBCamera,
    FBMatrix, FBModelNull, FBConstraintManager, FBModelTransformationType,
    FBFindModelByLabelName
)
from core.logger import logger
from mobu.utils import get_all_models, get_children

TOOL_NAME = "Auto Characterize"

# Global reference to prevent garbage collection
_auto_characterize_dialog = None


# Standard bone name mappings - Common naming conventions
BONE_NAME_PATTERNS = {
    "Hips": ["hips", "pelvis", "root", "hip"],
    "Spine": ["spine", "spine1", "spine_01"],
    "Spine1": ["spine1", "spine2", "spine_02"],
    "Spine2": ["spine2", "spine3", "spine_03"],
    "Spine3": ["spine3", "spine4", "spine_04"],
    "Neck": ["neck", "neck1"],
    "Head": ["head"],

    # Left Arm
    "LeftShoulder": ["leftshoulder", "l_shoulder", "shoulder_l", "clavicle_l", "l_clavicle"],
    "LeftArm": ["leftarm", "l_arm", "arm_l", "upperarm_l", "l_upperarm"],
    "LeftForeArm": ["leftforearm", "l_forearm", "forearm_l", "lowerarm_l", "l_lowerarm"],
    "LeftHand": ["lefthand", "l_hand", "hand_l"],

    # Right Arm
    "RightShoulder": ["rightshoulder", "r_shoulder", "shoulder_r", "clavicle_r", "r_clavicle"],
    "RightArm": ["rightarm", "r_arm", "arm_r", "upperarm_r", "r_upperarm"],
    "RightForeArm": ["rightforearm", "r_forearm", "forearm_r", "lowerarm_r", "r_lowerarm"],
    "RightHand": ["righthand", "r_hand", "hand_r"],

    # Left Leg
    "LeftUpLeg": ["leftupleg", "l_upleg", "upleg_l", "thigh_l", "l_thigh"],
    "LeftLeg": ["leftleg", "l_leg", "leg_l", "calf_l", "l_calf"],
    "LeftFoot": ["leftfoot", "l_foot", "foot_l"],

    # Right Leg
    "RightUpLeg": ["rightupleg", "r_upleg", "upleg_r", "thigh_r", "r_thigh"],
    "RightLeg": ["rightleg", "r_leg", "leg_r", "calf_r", "r_calf"],
    "RightFoot": ["rightfoot", "r_foot", "foot_r"],
}


def get_mobu_main_window():
    """Get MotionBuilder's main window to use as parent"""
    try:
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                if widget.objectName() == "MotionBuilder" or "MotionBuilder" in widget.windowTitle():
                    return widget
            widgets = app.topLevelWidgets()
            if widgets:
                return widgets[0]
        return None
    except Exception as e:
        print(f"[Auto Characterize] Error finding parent: {str(e)}")
        return None


def execute(control, event):
    """Execute the Auto Characterize tool"""
    global _auto_characterize_dialog

    if _auto_characterize_dialog is not None:
        print("[Auto Characterize] Bringing existing dialog to front")
        _auto_characterize_dialog.show()
        _auto_characterize_dialog.raise_()
        _auto_characterize_dialog.activateWindow()
        return

    print("[Auto Characterize] Creating new dialog")
    parent = get_mobu_main_window()
    _auto_characterize_dialog = AutoCharacterizeDialog(parent)
    _auto_characterize_dialog.show()


class AutoCharacterizeDialog(QDialog):
    """Auto-Characterization dialog"""

    def __init__(self, parent=None):
        super(AutoCharacterizeDialog, self).__init__(parent)

        if parent:
            self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)
        else:
            self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)

        self.setWindowTitle("Auto Characterize")
        self.resize(500, 400)
        self.setMinimumSize(500, 400)

        self.character = None
        self.detected_bones = {}
        self.root_object = None

        self.build_ui()

    def build_ui(self):
        """Build the UI"""
        layout = QtWidgets.QVBoxLayout(self)

        # Instructions
        instructions = QtWidgets.QLabel(
            "This tool will automatically:\n"
            "1. Detect skeleton bones by name patterns\n"
            "2. Analyze pose (T-pose vs A-pose)\n"
            "3. Apply T-pose if needed\n"
            "4. Create and characterize the character"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Root selection group
        root_group = QtWidgets.QGroupBox("Skeleton Root")
        root_layout = QtWidgets.QVBoxLayout()

        root_help = QtWidgets.QLabel("Select the root of your skeleton hierarchy (optional - will auto-detect if not specified)")
        root_help.setWordWrap(True)
        root_layout.addWidget(root_help)

        root_select_layout = QtWidgets.QHBoxLayout()
        self.root_label = QtWidgets.QLabel("<No root selected>")
        root_select_layout.addWidget(self.root_label)

        self.select_root_btn = QtWidgets.QPushButton("Use Selected")
        self.select_root_btn.clicked.connect(self.on_select_root)
        root_select_layout.addWidget(self.select_root_btn)

        root_layout.addLayout(root_select_layout)
        root_group.setLayout(root_layout)
        layout.addWidget(root_group)

        # Detection options
        options_group = QtWidgets.QGroupBox("Detection Options")
        options_layout = QtWidgets.QVBoxLayout()

        self.case_sensitive_check = QtWidgets.QCheckBox("Case sensitive name matching")
        self.case_sensitive_check.setChecked(False)
        options_layout.addWidget(self.case_sensitive_check)

        self.auto_tpose_check = QtWidgets.QCheckBox("Automatically apply T-pose if needed")
        self.auto_tpose_check.setChecked(True)
        options_layout.addWidget(self.auto_tpose_check)

        self.create_ik_fk_check = QtWidgets.QCheckBox("Create IK/FK Control Rig")
        self.create_ik_fk_check.setChecked(True)
        options_layout.addWidget(self.create_ik_fk_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Character name
        name_group = QtWidgets.QGroupBox("Character Name")
        name_layout = QtWidgets.QHBoxLayout()

        self.char_name_edit = QtWidgets.QLineEdit("Character")
        name_layout.addWidget(self.char_name_edit)

        name_group.setLayout(name_layout)
        layout.addWidget(name_group)

        # Progress/Status
        self.status_text = QtWidgets.QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(150)
        layout.addWidget(self.status_text)

        # Action buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.detect_btn = QtWidgets.QPushButton("1. Detect Skeleton")
        self.detect_btn.clicked.connect(self.on_detect_skeleton)
        button_layout.addWidget(self.detect_btn)

        self.characterize_btn = QtWidgets.QPushButton("2. Characterize")
        self.characterize_btn.clicked.connect(self.on_characterize)
        self.characterize_btn.setEnabled(False)
        button_layout.addWidget(self.characterize_btn)

        self.auto_btn = QtWidgets.QPushButton("Auto (All Steps)")
        self.auto_btn.clicked.connect(self.on_auto_characterize)
        self.auto_btn.setStyleSheet("font-weight: bold;")
        button_layout.addWidget(self.auto_btn)

        layout.addLayout(button_layout)

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def log(self, message):
        """Add message to status text"""
        self.status_text.append(message)
        print(f"[Auto Characterize] {message}")

    def closeEvent(self, event):
        """Handle dialog close event"""
        global _auto_characterize_dialog
        _auto_characterize_dialog = None
        event.accept()

    def on_select_root(self):
        """Use currently selected object as root"""
        from pyfbsdk import FBGetSelectedModels

        selected = FBGetSelectedModels()
        if not selected or len(selected) == 0:
            QMessageBox.warning(self, "No Selection", "Please select a root object in the viewport")
            return

        self.root_object = selected[0]
        self.root_label.setText(self.root_object.Name)
        self.log(f"Root set to: {self.root_object.Name}")

    def find_bone_by_patterns(self, slot_name, models, case_sensitive=False):
        """Find a bone using name pattern matching"""
        patterns = BONE_NAME_PATTERNS.get(slot_name, [])

        for model in models:
            model_name = model.Name if case_sensitive else model.Name.lower()

            for pattern in patterns:
                pattern_check = pattern if case_sensitive else pattern.lower()

                # Check if pattern matches (contains or exact match)
                if pattern_check in model_name or model_name == pattern_check:
                    return model

        return None

    def detect_skeleton_bones(self):
        """Automatically detect skeleton bones using name patterns"""
        self.log("=" * 50)
        self.log("Starting skeleton detection...")

        # Get models to search
        if self.root_object:
            self.log(f"Searching within root: {self.root_object.Name}")
            models = get_children(self.root_object, recursive=True)
            models.insert(0, self.root_object)  # Include root itself
        else:
            self.log("No root specified - searching all scene objects")
            models = get_all_models()

        # Filter out cameras
        models = [m for m in models if not isinstance(m, FBCamera)]
        self.log(f"Searching {len(models)} objects...")

        case_sensitive = self.case_sensitive_check.isChecked()

        # Detect bones
        self.detected_bones = {}
        for slot_name in BONE_NAME_PATTERNS.keys():
            bone = self.find_bone_by_patterns(slot_name, models, case_sensitive)
            if bone:
                self.detected_bones[slot_name] = bone
                self.log(f"✓ {slot_name}: {bone.Name}")

        # Check for required bones
        required = ["Hips", "Spine", "LeftUpLeg", "RightUpLeg"]
        missing = [slot for slot in required if slot not in self.detected_bones]

        if missing:
            self.log(f"⚠ WARNING: Missing required bones: {', '.join(missing)}")
            return False

        self.log(f"✓ Detection complete! Found {len(self.detected_bones)} bones")
        return True

    def check_tpose_vs_apose(self):
        """Check if arms are in T-pose or A-pose"""
        left_arm = self.detected_bones.get("LeftArm")
        right_arm = self.detected_bones.get("RightArm")

        if not left_arm or not right_arm:
            return True, "Cannot check pose - arm bones not detected"

        # Get arm rotations
        left_rot_y = abs(left_arm.Rotation[1])
        right_rot_y = abs(right_arm.Rotation[1])

        threshold = 20.0

        if left_rot_y > threshold or right_rot_y > threshold:
            return False, f"A-pose detected (LeftArm Y:{left_rot_y:.1f}°, RightArm Y:{right_rot_y:.1f}°)"

        return True, "T-pose detected"

    def apply_tpose(self):
        """Apply T-pose using IK-based method"""
        self.log("Applying T-pose...")

        # Center character
        hips = self.detected_bones.get("Hips")
        if hips:
            hips_vec = FBVector3d()
            hips.GetVector(hips_vec, FBModelTransformationType.kModelTranslation, True)
            centered_hips = FBVector3d(0.0, hips_vec[1], 0.0)
            hips.SetVector(centered_hips, FBModelTransformationType.kModelTranslation, True)
            self.log(f"Centered character at origin")

        # Zero all rotations
        for slot_name, model in self.detected_bones.items():
            if model:
                model.Rotation = FBVector3d(0, 0, 0)
        FBSystem().Scene.Evaluate()
        self.log("Zeroed all skeleton rotations")

        # T-pose limbs
        self._tpose_limb("LeftArm", "LeftForeArm", "LeftHand", is_arm=True)
        self._tpose_limb("RightArm", "RightForeArm", "RightHand", is_arm=True)
        self._tpose_limb("LeftUpLeg", "LeftLeg", "LeftFoot", is_arm=False)
        self._tpose_limb("RightUpLeg", "RightLeg", "RightFoot", is_arm=False)

        FBSystem().Scene.Evaluate()
        self.log("✓ T-pose applied successfully")

    def _tpose_limb(self, first_slot, mid_slot, end_slot, is_arm=True):
        """T-pose a limb using IK constraints"""
        first_joint = self.detected_bones.get(first_slot)
        mid_joint = self.detected_bones.get(mid_slot)
        end_joint = self.detected_bones.get(end_slot)

        if not (first_joint and mid_joint and end_joint):
            self.log(f"Skipping {first_slot} - not fully mapped")
            return

        # Create IK effector
        effector_name = f"TempIK_{end_joint.Name}_Effector"
        effector = FBModelNull(effector_name)
        effector.Show = True
        effector.Size = 50

        end_vec = FBVector3d()
        end_joint.GetVector(end_vec, FBModelTransformationType.kModelTranslation, True)
        effector.SetVector(end_vec, FBModelTransformationType.kModelTranslation, True)

        # Create pole vector
        pv_name = f"TempIK_{end_joint.Name}_PoleVector"
        pv = FBModelNull(pv_name)
        pv.Show = True
        pv.Size = 50

        mid_matrix = FBMatrix()
        mid_joint.GetMatrix(mid_matrix)
        pv.SetMatrix(mid_matrix)

        # Create Chain IK constraint
        constraint_mgr = FBConstraintManager()
        chain_ik = None

        for i in range(constraint_mgr.TypeGetCount()):
            if constraint_mgr.TypeGetName(i) == "Chain IK":
                chain_ik = constraint_mgr.TypeCreateConstraint(i)
                chain_ik.Name = f"TempIK_{end_joint.Name}"
                break

        if chain_ik:
            # Add references
            for ref_idx in range(chain_ik.ReferenceGroupGetCount()):
                group_name = chain_ik.ReferenceGroupGetName(ref_idx)
                if group_name == "First Joint":
                    chain_ik.ReferenceAdd(ref_idx, first_joint)
                elif group_name == "End Joint":
                    chain_ik.ReferenceAdd(ref_idx, end_joint)
                elif group_name == "Effector":
                    chain_ik.ReferenceAdd(ref_idx, effector)
                elif group_name == "Pole Vector Object":
                    chain_ik.ReferenceAdd(ref_idx, pv)

            chain_ik.Snap()

            # Calculate limb length
            limb_length = abs(mid_joint.Translation[1]) + abs(end_joint.Translation[1])

            # Get first joint world position
            first_vec = FBVector3d()
            first_joint.GetVector(first_vec, FBModelTransformationType.kModelTranslation, True)

            # Position effector for T-pose
            if is_arm:
                if first_vec[0] < 0:  # Left arm
                    x_offset = first_vec[0] - limb_length
                else:  # Right arm
                    x_offset = first_vec[0] + limb_length

                ik_offset = FBVector3d(x_offset, first_vec[1], first_vec[2])
                pv_offset = FBVector3d(first_vec[0], first_vec[1], -50)
            else:
                # Legs
                y_offset = first_vec[1] - limb_length
                ik_offset = FBVector3d(first_vec[0], y_offset, first_vec[2])
                pv_offset = FBVector3d(first_vec[0], first_vec[1], 50)

            # Apply positions
            effector.SetVector(ik_offset, FBModelTransformationType.kModelTranslation, True)
            pv.SetVector(pv_offset, FBModelTransformationType.kModelTranslation, True)
            pv.SetVector(FBVector3d(0, 0, 0), FBModelTransformationType.kModelRotation, True)

            FBSystem().Scene.Evaluate()

            # Clean up
            chain_ik.Active = False
            chain_ik.FBDelete()
            effector.FBDelete()
            pv.FBDelete()

    def create_character(self):
        """Create and characterize the character"""
        char_name = self.char_name_edit.text() or "Character"
        self.log(f"Creating character: {char_name}")

        # Create character
        self.character = FBCharacter(char_name)
        self.character.SetCharacterizeOn(False)

        # Map bones
        mapped_count = 0
        for slot_name, model in self.detected_bones.items():
            if model:
                prop_list = self.character.PropertyList.Find(slot_name + "Link")
                if prop_list:
                    prop_list.append(model)
                    mapped_count += 1

        self.log(f"Mapped {mapped_count} bones to character")

        # Characterize
        self.log("Characterizing...")
        self.character.SetCharacterizeOn(True)  # True = Biped

        if self.character.GetCharacterizeError():
            error_msg = self.character.GetCharacterizeError()
            self.log(f"✗ Characterization failed: {error_msg}")
            raise Exception(error_msg)

        self.log("✓ Characterization successful!")

        # Create Control Rig if requested
        if self.create_ik_fk_check.isChecked():
            self.log("Creating IK/FK Control Rig...")
            if self.character.CreateControlRig(True):
                self.log("✓ Control Rig created!")
            else:
                self.log("⚠ Control Rig creation failed")

        return True

    def on_detect_skeleton(self):
        """Detect skeleton bones"""
        self.status_text.clear()

        if self.detect_skeleton_bones():
            self.characterize_btn.setEnabled(True)
            QMessageBox.information(
                self,
                "Detection Complete",
                f"Successfully detected {len(self.detected_bones)} bones!\n\n"
                f"You can now proceed to characterization."
            )
        else:
            QMessageBox.warning(
                self,
                "Detection Incomplete",
                "Could not find all required bones.\n\n"
                "Required: Hips, Spine, LeftUpLeg, RightUpLeg\n\n"
                "Try:\n"
                "• Selecting a skeleton root object\n"
                "• Adjusting case sensitivity setting"
            )

    def on_characterize(self):
        """Characterize the detected skeleton"""
        if not self.detected_bones:
            QMessageBox.warning(self, "No Detection", "Please detect skeleton first")
            return

        try:
            # Check T-pose
            is_tpose, pose_msg = self.check_tpose_vs_apose()
            self.log(pose_msg)

            if not is_tpose:
                if self.auto_tpose_check.isChecked():
                    self.apply_tpose()
                else:
                    reply = QMessageBox.question(
                        self,
                        "A-Pose Detected",
                        f"{pose_msg}\n\nApply T-pose automatically?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.apply_tpose()

            # Create character
            if self.create_character():
                QMessageBox.information(
                    self,
                    "Success",
                    f"Character '{self.character.Name}' created successfully!"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Characterization failed:\n{str(e)}"
            )
            logger.error(f"Characterization error: {str(e)}")

    def on_auto_characterize(self):
        """Run full automatic characterization"""
        self.status_text.clear()
        self.log("Starting automatic characterization...")

        try:
            # Step 1: Detect
            if not self.detect_skeleton_bones():
                QMessageBox.warning(
                    self,
                    "Detection Failed",
                    "Could not detect required skeleton bones.\n\n"
                    "Please check the status log for details."
                )
                return

            # Step 2: Check T-pose
            is_tpose, pose_msg = self.check_tpose_vs_apose()
            self.log(pose_msg)

            if not is_tpose and self.auto_tpose_check.isChecked():
                self.apply_tpose()

            # Step 3: Characterize
            if self.create_character():
                QMessageBox.information(
                    self,
                    "Success",
                    f"✓ Auto-characterization complete!\n\n"
                    f"Character: {self.character.Name}\n"
                    f"Bones detected: {len(self.detected_bones)}\n"
                    f"Type: Biped"
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Auto-characterization failed:\n{str(e)}\n\n"
                f"Check the status log for details."
            )
            logger.error(f"Auto-characterization error: {str(e)}")
            import traceback
            traceback.print_exc()
