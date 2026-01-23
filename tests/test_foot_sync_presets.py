"""
Unit tests for Foot Sync Preset Loading and Validation
Tests the character preset validation and loading system
"""

import unittest
import json
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the validation function (we'll mock pymxs)
import max.tools.animation.foot_sync as foot_sync_module


class TestPresetValidation(unittest.TestCase):
    """Test preset validation logic"""

    def test_valid_preset(self):
        """Test validation of a completely valid preset"""
        preset = {
            "description": "Test character",
            "height_cm": 175,
            "toe": {"min": 3.0, "neutral": 4.0, "max": 5.0},
            "feet": {"min": 14.0, "neutral": 15.0, "max": 16.0},
            "thresholds": {
                "angle_speed": 1.2,
                "min_movement": 0.22,
                "height_tolerance": 2.0,
                "speed_tolerance": 0.4
            },
            "motion_range": {"feet": 4.5, "toe": 1.4}
        }
        
        is_valid, warnings, errors = foot_sync_module.validate_preset("TestChar", preset)
        
        self.assertTrue(is_valid, "Valid preset should pass validation")
        self.assertEqual(len(errors), 0, "Valid preset should have no errors")

    def test_missing_toe_section(self):
        """Test validation catches missing toe section"""
        preset = {
            "feet": {"min": 14.0, "neutral": 15.0, "max": 16.0},
            "thresholds": {
                "angle_speed": 1.2,
                "min_movement": 0.22,
                "height_tolerance": 2.0,
                "speed_tolerance": 0.4
            },
            "motion_range": {"feet": 4.5, "toe": 1.4}
        }
        
        is_valid, warnings, errors = foot_sync_module.validate_preset("TestChar", preset)
        
        self.assertFalse(is_valid, "Preset missing toe section should fail")
        self.assertTrue(any("Missing required section: 'toe'" in e for e in errors))

    def test_missing_toe_min(self):
        """Test validation catches missing toe.min"""
        preset = {
            "toe": {"neutral": 4.0, "max": 5.0},
            "feet": {"min": 14.0, "neutral": 15.0, "max": 16.0},
            "thresholds": {
                "angle_speed": 1.2,
                "min_movement": 0.22,
                "height_tolerance": 2.0,
                "speed_tolerance": 0.4
            },
            "motion_range": {"feet": 4.5, "toe": 1.4}
        }
        
        is_valid, warnings, errors = foot_sync_module.validate_preset("TestChar", preset)
        
        self.assertFalse(is_valid, "Preset missing toe.min should fail")
        self.assertTrue(any("Missing toe.min" in e for e in errors))

    def test_invalid_type_for_toe_min(self):
        """Test validation catches wrong data type"""
        preset = {
            "toe": {"min": "not_a_number", "neutral": 4.0, "max": 5.0},
            "feet": {"min": 14.0, "neutral": 15.0, "max": 16.0},
            "thresholds": {
                "angle_speed": 1.2,
                "min_movement": 0.22,
                "height_tolerance": 2.0,
                "speed_tolerance": 0.4
            },
            "motion_range": {"feet": 4.5, "toe": 1.4}
        }
        
        is_valid, warnings, errors = foot_sync_module.validate_preset("TestChar", preset)
        
        self.assertFalse(is_valid, "Preset with string instead of number should fail")
        self.assertTrue(any("toe.min must be a number" in e for e in errors))

    def test_warning_for_inverted_min_max(self):
        """Test validation warns when min > max"""
        preset = {
            "toe": {"min": 10.0, "neutral": 4.0, "max": 1.0},  # Inverted!
            "feet": {"min": 14.0, "neutral": 15.0, "max": 16.0},
            "thresholds": {
                "angle_speed": 1.2,
                "min_movement": 0.22,
                "height_tolerance": 2.0,
                "speed_tolerance": 0.4
            },
            "motion_range": {"feet": 4.5, "toe": 1.4}
        }
        
        is_valid, warnings, errors = foot_sync_module.validate_preset("TestChar", preset)
        
        self.assertTrue(is_valid, "Inverted values should still be valid (just warned)")
        self.assertTrue(len(warnings) > 0, "Should have warnings about inverted values")
        self.assertTrue(any("toe.min" in w and "toe.max" in w for w in warnings))

    def test_negative_threshold_warning(self):
        """Test validation warns about negative thresholds"""
        preset = {
            "toe": {"min": 3.0, "neutral": 4.0, "max": 5.0},
            "feet": {"min": 14.0, "neutral": 15.0, "max": 16.0},
            "thresholds": {
                "angle_speed": -1.2,  # Negative!
                "min_movement": 0.22,
                "height_tolerance": 2.0,
                "speed_tolerance": 0.4
            },
            "motion_range": {"feet": 4.5, "toe": 1.4}
        }
        
        is_valid, warnings, errors = foot_sync_module.validate_preset("TestChar", preset)
        
        self.assertTrue(is_valid, "Negative threshold should still be valid (just warned)")
        self.assertTrue(len(warnings) > 0, "Should have warnings about negative values")
        self.assertTrue(any("angle_speed" in w and "negative" in w for w in warnings))

    def test_missing_multiple_fields(self):
        """Test validation catches multiple missing fields"""
        preset = {
            "toe": {"min": 3.0},  # Missing neutral and max
            "feet": {"neutral": 15.0},  # Missing min and max
            "thresholds": {
                "angle_speed": 1.2
                # Missing other thresholds
            },
            "motion_range": {}  # Missing both feet and toe
        }
        
        is_valid, warnings, errors = foot_sync_module.validate_preset("TestChar", preset)
        
        self.assertFalse(is_valid, "Preset with multiple missing fields should fail")
        self.assertGreater(len(errors), 5, "Should have multiple error messages")

    def test_out_of_range_values_warning(self):
        """Test validation warns about unusual value ranges"""
        preset = {
            "toe": {"min": 3.0, "neutral": 4.0, "max": 5.0},
            "feet": {"min": -500.0, "neutral": 15.0, "max": 2000.0},  # Unusual range
            "thresholds": {
                "angle_speed": 1.2,
                "min_movement": 0.22,
                "height_tolerance": 2.0,
                "speed_tolerance": 0.4
            },
            "motion_range": {"feet": 4.5, "toe": 1.4}
        }
        
        is_valid, warnings, errors = foot_sync_module.validate_preset("TestChar", preset)
        
        self.assertTrue(is_valid, "Out of typical range should still be valid")
        self.assertTrue(len(warnings) > 0, "Should have warnings about unusual ranges")


class TestPresetLoading(unittest.TestCase):
    """Test preset loading from JSON files"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_config(self, presets_dict):
        """Helper to create a test config file"""
        config = {
            "version": "1.0.0",
            "description": "Test config",
            "presets": presets_dict
        }
        
        config_path = Path(self.test_dir) / "foot_sync_presets.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        return config_path

    def test_load_valid_presets(self):
        """Test loading a file with valid presets"""
        presets = {
            "TestChar1": {
                "description": "Test 1",
                "toe": {"min": 3.0, "neutral": 4.0, "max": 5.0},
                "feet": {"min": 14.0, "neutral": 15.0, "max": 16.0},
                "thresholds": {
                    "angle_speed": 1.2,
                    "min_movement": 0.22,
                    "height_tolerance": 2.0,
                    "speed_tolerance": 0.4
                },
                "motion_range": {"feet": 4.5, "toe": 1.4}
            },
            "TestChar2": {
                "description": "Test 2",
                "toe": {"min": 2.0, "neutral": 3.0, "max": 4.0},
                "feet": {"min": 10.0, "neutral": 11.0, "max": 12.0},
                "thresholds": {
                    "angle_speed": 1.0,
                    "min_movement": 0.2,
                    "height_tolerance": 1.5,
                    "speed_tolerance": 0.3
                },
                "motion_range": {"feet": 3.5, "toe": 1.0}
            }
        }
        
        config_path = self.create_test_config(presets)
        
        # Mock the config path in the module
        original_path = foot_sync_module.Path(__file__).parent.parent.parent.parent / "config" / "foot_sync_presets.json"
        
        # Temporarily replace the path for testing
        # (In real scenario, we'd use dependency injection)
        # For now, just test validation directly
        
        # Validate both presets should pass
        is_valid1, _, errors1 = foot_sync_module.validate_preset("TestChar1", presets["TestChar1"])
        is_valid2, _, errors2 = foot_sync_module.validate_preset("TestChar2", presets["TestChar2"])
        
        self.assertTrue(is_valid1, "TestChar1 should be valid")
        self.assertTrue(is_valid2, "TestChar2 should be valid")

    def test_load_mixed_valid_invalid(self):
        """Test loading file with both valid and invalid presets"""
        presets = {
            "ValidChar": {
                "description": "Valid",
                "toe": {"min": 3.0, "neutral": 4.0, "max": 5.0},
                "feet": {"min": 14.0, "neutral": 15.0, "max": 16.0},
                "thresholds": {
                    "angle_speed": 1.2,
                    "min_movement": 0.22,
                    "height_tolerance": 2.0,
                    "speed_tolerance": 0.4
                },
                "motion_range": {"feet": 4.5, "toe": 1.4}
            },
            "InvalidChar": {
                "description": "Invalid - missing toe section",
                "feet": {"min": 14.0, "neutral": 15.0, "max": 16.0},
                "thresholds": {
                    "angle_speed": 1.2,
                    "min_movement": 0.22,
                    "height_tolerance": 2.0,
                    "speed_tolerance": 0.4
                },
                "motion_range": {"feet": 4.5, "toe": 1.4}
            }
        }
        
        # Validate separately
        is_valid1, _, _ = foot_sync_module.validate_preset("ValidChar", presets["ValidChar"])
        is_valid2, _, _ = foot_sync_module.validate_preset("InvalidChar", presets["InvalidChar"])
        
        self.assertTrue(is_valid1, "ValidChar should pass validation")
        self.assertFalse(is_valid2, "InvalidChar should fail validation")

    def test_malformed_json(self):
        """Test handling of malformed JSON file"""
        bad_json_path = Path(self.test_dir) / "bad.json"
        with open(bad_json_path, 'w') as f:
            f.write("{this is not valid json}")
        
        # Should handle gracefully
        try:
            with open(bad_json_path, 'r') as f:
                data = json.load(f)
            self.fail("Should have raised JSONDecodeError")
        except json.JSONDecodeError as e:
            self.assertIsNotNone(e, "Should catch JSON decode error")


class TestMaxScriptConversion(unittest.TestCase):
    """Test conversion of presets to MaxScript format"""

    def test_convert_single_preset(self):
        """Test converting a single preset to MaxScript"""
        presets = {
            "TestChar": {
                "description": "Test",
                "toe": {"min": 3.0, "neutral": 4.0, "max": 5.0},
                "feet": {"min": 14.0, "neutral": 15.0, "max": 16.0},
                "thresholds": {
                    "angle_speed": 1.2,
                    "min_movement": 0.22,
                    "height_tolerance": 2.0,
                    "speed_tolerance": 0.4
                },
                "motion_range": {"feet": 4.5, "toe": 1.4}
            }
        }
        
        ms_code = foot_sync_module.convert_presets_to_maxscript(presets)
        
        self.assertIn("#(", ms_code, "Should start with MaxScript array")
        self.assertIn('"TestChar"', ms_code, "Should contain character name")
        self.assertIn("toe_min", ms_code, "Should contain parameter names")
        self.assertIn("3.0", ms_code, "Should contain parameter values")

    def test_convert_multiple_presets(self):
        """Test converting multiple presets"""
        presets = {
            "Char1": {
                "toe": {"min": 3.0, "neutral": 4.0, "max": 5.0},
                "feet": {"min": 14.0, "neutral": 15.0, "max": 16.0},
                "thresholds": {
                    "angle_speed": 1.2,
                    "min_movement": 0.22,
                    "height_tolerance": 2.0,
                    "speed_tolerance": 0.4
                },
                "motion_range": {"feet": 4.5, "toe": 1.4}
            },
            "Char2": {
                "toe": {"min": 2.0, "neutral": 3.0, "max": 4.0},
                "feet": {"min": 10.0, "neutral": 11.0, "max": 12.0},
                "thresholds": {
                    "angle_speed": 1.0,
                    "min_movement": 0.2,
                    "height_tolerance": 1.5,
                    "speed_tolerance": 0.3
                },
                "motion_range": {"feet": 3.5, "toe": 1.0}
            }
        }
        
        ms_code = foot_sync_module.convert_presets_to_maxscript(presets)
        
        self.assertIn('"Char1"', ms_code, "Should contain first character")
        self.assertIn('"Char2"', ms_code, "Should contain second character")
        self.assertIn("3.0", ms_code, "Should contain Char1 values")
        self.assertIn("2.0", ms_code, "Should contain Char2 values")


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPresetValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestPresetLoading))
    suite.addTests(loader.loadTestsFromTestCase(TestMaxScriptConversion))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
