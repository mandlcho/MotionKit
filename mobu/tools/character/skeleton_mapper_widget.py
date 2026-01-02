"""
Visual Skeleton Mapper Widget
Displays a skeleton diagram where users can drag and drop bones to map them
"""

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from PySide2.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem
    from PySide2.QtCore import Qt, QRectF, QPointF, Signal
    from PySide2.QtGui import QColor, QPen, QBrush, QFont
except ImportError:
    try:
        from PySide import QtGui as QtWidgets
        from PySide import QtCore, QtGui
        from PySide.QtGui import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem
        from PySide.QtCore import Qt, QRectF, QPointF, Signal
        from PySide.QtGui import QColor, QPen, QBrush, QFont
    except ImportError:
        print("[Skeleton Mapper Widget] ERROR: Neither PySide2 nor PySide found")


class BoneRegion(QGraphicsRectItem):
    """A clickable region representing a bone slot in the skeleton"""

    def __init__(self, bone_name, x, y, width, height):
        super(BoneRegion, self).__init__(x, y, width, height)
        self.bone_name = bone_name
        self.mapped_bone = None

        # Visual styling
        self.default_pen = QPen(QColor(100, 100, 100))
        self.hover_pen = QPen(QColor(0, 120, 215), 2)
        self.mapped_pen = QPen(QColor(0, 200, 0), 2)

        self.default_brush = QBrush(QColor(50, 50, 50, 100))
        self.hover_brush = QBrush(QColor(0, 120, 215, 50))
        self.mapped_brush = QBrush(QColor(0, 200, 0, 100))

        self.setPen(self.default_pen)
        self.setBrush(self.default_brush)

        # Enable hover events
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)

        # Add text label
        self.label = QGraphicsTextItem(bone_name, self)
        self.label.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Arial", 8)
        self.label.setFont(font)

        # Center the label
        label_rect = self.label.boundingRect()
        self.label.setPos(
            width / 2 - label_rect.width() / 2,
            height / 2 - label_rect.height() / 2
        )

    def hoverEnterEvent(self, event):
        """Handle mouse hover enter"""
        if not self.mapped_bone:
            self.setPen(self.hover_pen)
            self.setBrush(self.hover_brush)
        super(BoneRegion, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Handle mouse hover leave"""
        if not self.mapped_bone:
            self.setPen(self.default_pen)
            self.setBrush(self.default_brush)
        super(BoneRegion, self).hoverLeaveEvent(event)

    def set_mapped_bone(self, bone_model):
        """Set the bone that's mapped to this region"""
        self.mapped_bone = bone_model
        if bone_model:
            self.setPen(self.mapped_pen)
            self.setBrush(self.mapped_brush)
            # Update label to show bone name
            self.label.setPlainText(f"{self.bone_name}:\n{bone_model.Name}")
        else:
            self.setPen(self.default_pen)
            self.setBrush(self.default_brush)
            self.label.setPlainText(self.bone_name)

    def clear_mapping(self):
        """Clear the bone mapping"""
        self.set_mapped_bone(None)


class SkeletonMapperWidget(QGraphicsView):
    """Visual skeleton mapper with drag & drop bone assignment"""

    # Signal emitted when a bone is mapped: (bone_slot_name, model)
    bone_mapped = Signal(str, object)

    def __init__(self, parent=None):
        super(SkeletonMapperWidget, self).__init__(parent)

        self.bone_regions = {}
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Configure view
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(40, 40, 40)))
        self.setMinimumHeight(600)

        # Enable drag & drop
        self.setAcceptDrops(True)

        # Build the skeleton
        self._build_skeleton()

    def _build_skeleton(self):
        """Build the visual skeleton with clickable regions"""
        # Layout dimensions
        center_x = 150
        slot_width = 80
        slot_height = 30
        v_spacing = 5
        h_spacing = 20

        # Define bone positions (x, y relative to layout)
        bone_positions = {
            # Reference (top)
            "Reference": (center_x - slot_width/2, 20),

            # Head and Neck
            "Head": (center_x - slot_width/2, 60),
            "Neck": (center_x - slot_width/2, 60 + slot_height + v_spacing),

            # Spine (center column)
            "Spine": (center_x - slot_width/2, 120),
            "Spine1": (center_x - slot_width/2, 120 + (slot_height + v_spacing) * 1),
            "Spine2": (center_x - slot_width/2, 120 + (slot_height + v_spacing) * 2),
            "Spine3": (center_x - slot_width/2, 120 + (slot_height + v_spacing) * 3),
            "Hips": (center_x - slot_width/2, 120 + (slot_height + v_spacing) * 4),

            # Left Arm
            "LeftShoulder": (center_x - slot_width - h_spacing, 120),
            "LeftArm": (center_x - slot_width - h_spacing, 120 + (slot_height + v_spacing) * 1),
            "LeftForeArm": (center_x - slot_width - h_spacing, 120 + (slot_height + v_spacing) * 2),
            "LeftHand": (center_x - slot_width - h_spacing, 120 + (slot_height + v_spacing) * 3),

            # Right Arm
            "RightShoulder": (center_x + h_spacing, 120),
            "RightArm": (center_x + h_spacing, 120 + (slot_height + v_spacing) * 1),
            "RightForeArm": (center_x + h_spacing, 120 + (slot_height + v_spacing) * 2),
            "RightHand": (center_x + h_spacing, 120 + (slot_height + v_spacing) * 3),

            # Left Leg
            "LeftUpLeg": (center_x - slot_width/2 - h_spacing, 300),
            "LeftLeg": (center_x - slot_width/2 - h_spacing, 300 + (slot_height + v_spacing) * 1),
            "LeftFoot": (center_x - slot_width/2 - h_spacing, 300 + (slot_height + v_spacing) * 2),

            # Right Leg
            "RightUpLeg": (center_x - slot_width/2 + h_spacing, 300),
            "RightLeg": (center_x - slot_width/2 + h_spacing, 300 + (slot_height + v_spacing) * 1),
            "RightFoot": (center_x - slot_width/2 + h_spacing, 300 + (slot_height + v_spacing) * 2),
        }

        # Create bone regions
        for bone_name, (x, y) in bone_positions.items():
            region = BoneRegion(bone_name, x, y, slot_width, slot_height)
            self.bone_regions[bone_name] = region
            self.scene.addItem(region)

        # Set scene rect to fit all regions
        self.scene.setSceneRect(0, 0, 400, 450)

    def dragEnterEvent(self, event):
        """Handle drag enter"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """Handle drag move"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle drop onto the skeleton"""
        if event.mimeData().hasText():
            # Get the bone name from drop
            dropped_bone_name = event.mimeData().text()

            # Find which bone region was dropped on
            drop_pos = self.mapToScene(event.pos())
            items = self.scene.items(drop_pos)

            for item in items:
                if isinstance(item, BoneRegion):
                    # Emit signal so parent can handle the mapping
                    self.bone_mapped.emit(item.bone_name, dropped_bone_name)
                    event.acceptProposedAction()
                    return

            event.ignore()
        else:
            event.ignore()

    def set_bone_mapping(self, bone_slot, model):
        """Set a bone mapping (called from parent dialog)"""
        if bone_slot in self.bone_regions:
            self.bone_regions[bone_slot].set_mapped_bone(model)

    def clear_bone_mapping(self, bone_slot):
        """Clear a bone mapping"""
        if bone_slot in self.bone_regions:
            self.bone_regions[bone_slot].clear_mapping()

    def clear_all_mappings(self):
        """Clear all bone mappings"""
        for region in self.bone_regions.values():
            region.clear_mapping()
