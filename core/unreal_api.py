"""
Shared Unreal Engine API Client
Uses Unreal's Web Remote Control for communication
Works with both 3ds Max and MotionBuilder
"""

import json
from pathlib import Path

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("[Unreal API] Warning: requests module not available, HTTP features disabled")

from core.logger import logger
from core.config import config


class UnrealAPI:
    """
    Client for Unreal Engine Web Remote Control API

    Requires:
    - Unreal Engine running
    - Web Remote Control plugin enabled
    - Remote Control API enabled in Project Settings
    """

    def __init__(self, host="127.0.0.1", port=30010):
        """
        Initialize Unreal API client

        Args:
            host: Unreal Engine host (default: localhost)
            port: Web Remote Control port (default: 30010)
        """
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.timeout = 10

    def is_connected(self):
        """Check if Unreal Engine is running and Web Remote Control is active"""
        if not REQUESTS_AVAILABLE:
            return False

        try:
            response = requests.get(
                f"{self.base_url}/remote/info",
                timeout=2
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Unreal connection check failed: {str(e)}")
            return False

    def execute_python(self, python_code):
        """
        Execute Python code in Unreal Engine

        Args:
            python_code: Python code string to execute

        Returns:
            dict: Response from Unreal, or None if failed
        """
        if not REQUESTS_AVAILABLE:
            logger.error("requests module not available")
            return None

        try:
            url = f"{self.base_url}/remote/object/call"

            payload = {
                "objectPath": "/Script/PythonScriptPlugin.Default__PythonScriptLibrary",
                "functionName": "ExecutePythonCommand",
                "parameters": {
                    "PythonCommand": python_code
                },
                "generateTransaction": False
            }

            response = requests.put(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.debug(f"Python execution successful")
                return response.json()
            else:
                logger.error(f"Python execution failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Failed to execute Python in Unreal: {str(e)}")
            return None

    def reimport_assets(self, asset_paths):
        """
        Reimport existing assets in Unreal

        Args:
            asset_paths: List of Unreal asset paths (e.g., ["/Game/Animations/Idle"])

        Returns:
            bool: True if successful
        """
        if not asset_paths:
            return True

        logger.info(f"Reimporting {len(asset_paths)} assets in Unreal...")

        # Build Python command
        paths_list = json.dumps(asset_paths)
        python_code = f'''
import unreal

asset_paths = {paths_list}
reimported = []
failed = []

for asset_path in asset_paths:
    try:
        # Load the asset
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            unreal.log(f"Reimporting: {{asset_path}}")

            # Trigger reimport
            success = unreal.EditorAssetLibrary.reimport_asset(asset_path)

            if success:
                reimported.append(asset_path)
            else:
                failed.append(asset_path)
                unreal.log_warning(f"Reimport failed: {{asset_path}}")
        else:
            failed.append(asset_path)
            unreal.log_warning(f"Asset not found: {{asset_path}}")
    except Exception as e:
        failed.append(asset_path)
        unreal.log_error(f"Error reimporting {{asset_path}}: {{str(e)}}")

unreal.log(f"Reimport complete: {{len(reimported)}} succeeded, {{len(failed)}} failed")
'''

        result = self.execute_python(python_code)
        success = result is not None

        if success:
            logger.info(f"Reimport request sent successfully")
        else:
            logger.error("Failed to send reimport request")

        return success

    def import_fbx_files(self, fbx_files, destination_path="/Game/Animations", skeleton_path=None):
        """
        Import FBX files into Unreal Engine

        Args:
            fbx_files: List of FBX file paths (absolute paths)
            destination_path: Unreal content browser destination
            skeleton_path: Optional skeleton asset path for animations

        Returns:
            bool: True if successful
        """
        if not fbx_files:
            return True

        logger.info(f"Importing {len(fbx_files)} FBX files into Unreal...")

        # Convert paths to forward slashes and escape
        files_list = [str(Path(f)).replace('\\', '/') for f in fbx_files]
        files_json = json.dumps(files_list)

        python_code = f'''
import unreal

# FBX files to import
fbx_files = {files_json}
destination = "{destination_path}"
skeleton_path = {json.dumps(skeleton_path)}

# Setup import options
options = unreal.FbxImportUI()
options.import_mesh = False
options.import_animations = True
options.import_as_skeletal = False
options.import_materials = False
options.import_textures = False
options.automated_import_should_detect_type = False

# Animation import options
anim_import_data = options.anim_sequence_import_data
anim_import_data.animation_length = unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME
anim_import_data.import_meshes_in_bone_hierarchy = False
anim_import_data.use_default_sample_rate = False
anim_import_data.custom_sample_rate = 30
anim_import_data.import_custom_attribute = True
anim_import_data.import_bone_tracks = True
anim_import_data.remove_redundant_keys = False
anim_import_data.do_not_import_curve_with_zero = False
anim_import_data.preserve_local_transform = False

# Set skeleton if provided
if skeleton_path:
    skeleton = unreal.load_asset(skeleton_path)
    if skeleton:
        options.skeleton = skeleton
        unreal.log(f"Using skeleton: {{skeleton_path}}")
    else:
        unreal.log_warning(f"Skeleton not found: {{skeleton_path}}")

# Import files
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
imported_assets = []
failed_imports = []

for fbx_file in fbx_files:
    try:
        import_task = unreal.AssetImportTask()
        import_task.filename = fbx_file
        import_task.destination_path = destination
        import_task.automated = True
        import_task.save = True
        import_task.replace_existing = True
        import_task.options = options

        unreal.log(f"Importing: {{fbx_file}} -> {{destination}}")
        asset_tools.import_asset_tasks([import_task])

        if import_task.imported_object_paths:
            for imported in import_task.imported_object_paths:
                imported_assets.append(imported)
                unreal.log(f"Imported: {{imported}}")
        else:
            failed_imports.append(fbx_file)
            unreal.log_warning(f"Import failed: {{fbx_file}}")
    except Exception as e:
        failed_imports.append(fbx_file)
        unreal.log_error(f"Error importing {{fbx_file}}: {{str(e)}}")

unreal.log(f"Import complete: {{len(imported_assets)}} succeeded, {{len(failed_imports)}} failed")
'''

        result = self.execute_python(python_code)
        success = result is not None

        if success:
            logger.info(f"Import request sent successfully")
        else:
            logger.error("Failed to send import request")

        return success


def get_unreal_api():
    """Get or create Unreal API client instance"""
    host = config.get('unreal.host', '127.0.0.1')
    port = config.get('unreal.port', 30010)

    return UnrealAPI(host=host, port=port)
