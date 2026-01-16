"""
Test script for MotionBuilder selection utilities

This script demonstrates the usage of the selection utilities.
Run this in MotionBuilder's Python Editor to test the functions.

Usage:
    1. Select some objects in MotionBuilder
    2. Run this script in the Python Editor
    3. Check the output to see the selection utilities in action
"""

if __name__ == "__main__":
    # Add project root to path if needed
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

try:
    from mobu.utils import (
        get_selection,
        get_selection_as_list,
        get_selection_names,
        get_first_selected,
        get_last_selected,
        get_selection_count,
        validate_selection,
        find_model_by_name,
        find_models_by_pattern
    )

    print("\n" + "="*60)
    print("MotionBuilder Selection Utilities Test")
    print("="*60)

    # Test 1: Get selection count
    count = get_selection_count()
    print(f"\n1. Selection Count: {count}")

    if count == 0:
        print("\n   No objects selected! Please select some objects and run again.")
    else:
        # Test 2: Get selection names (ordered)
        names = get_selection_names(sort_by_order=True)
        print(f"\n2. Selected Objects (in order):")
        for i, name in enumerate(names, 1):
            print(f"   {i}. {name}")

        # Test 3: Get first and last selected
        first = get_first_selected()
        last = get_last_selected()
        print(f"\n3. First Selected: {first.Name if first else 'None'}")
        print(f"   Last Selected: {last.Name if last else 'None'}")

        # Test 4: Get selection as list
        selection_list = get_selection_as_list(sort_by_order=True)
        print(f"\n4. Selection as Python List:")
        print(f"   Type: {type(selection_list)}")
        print(f"   Length: {len(selection_list)}")

        # Test 5: Validate selection
        print(f"\n5. Validation Tests:")
        print(f"   At least 1 selected: {validate_selection(min_count=1)}")
        print(f"   At least 2 selected: {validate_selection(min_count=2)}")
        print(f"   Between 1-5 selected: {validate_selection(min_count=1, max_count=5)}")

        # Test 6: Get selection order comparison
        print(f"\n6. Selection Order Test:")
        unordered = get_selection_as_list(sort_by_order=False)
        ordered = get_selection_as_list(sort_by_order=True)
        print(f"   Unordered names: {[m.Name for m in unordered]}")
        print(f"   Ordered names: {[m.Name for m in ordered]}")

        # Test 7: Find models by pattern (if any controls exist)
        print(f"\n7. Pattern Matching Test:")
        try:
            first_obj = first.Name if first else ""
            if first_obj:
                # Try to find objects with similar patterns
                pattern_results = find_models_by_pattern(first_obj[:3] + "*")
                print(f"   Pattern '{first_obj[:3]}*' found {len(pattern_results)} objects")
                if pattern_results:
                    print(f"   Sample: {pattern_results[0].Name}")
            else:
                print("   Skipping pattern test - no selection")
        except Exception as e:
            print(f"   Pattern test error: {e}")

    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60 + "\n")

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
