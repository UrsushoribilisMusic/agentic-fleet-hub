#!/usr/bin/env python3
"""Test script for heartbeat optimization"""
import subprocess
import time
import os

def test_optimization():
    print("Testing heartbeat optimization...")
    
    # First run - should read MISSION_CONTROL.md
    print("\n1. First run (should read MISSION_CONTROL.md):")
    result1 = subprocess.run(["python3", "~/fleet/misty/heartbeat_optimize.py"], 
                          capture_output=True, text=True)
    print(f"   Exit code: {result1.returncode}")
    print(f"   Output: {result1.stdout.strip()}")
    
    # Second run - should skip reading MISSION_CONTROL.md
    print("\n2. Second run (should skip MISSION_CONTROL.md):")
    result2 = subprocess.run(["python3", "~/fleet/misty/heartbeat_optimize.py"], 
                          capture_output=True, text=True)
    print(f"   Exit code: {result2.returncode}")
    print(f"   Output: {result2.stdout.strip()}")
    
    # Modify MISSION_CONTROL.md
    print("\n3. Modifying MISSION_CONTROL.md...")
    mc_path = "/Users/miguelrodriguez/fleet/MISSION_CONTROL.md"
    with open(mc_path, "a") as f:
        f.write("\n# TEST COMMENT - This will trigger a checksum change\n")
    
    # Third run - should read MISSION_CONTROL.md again
    print("\n4. Third run (should read MISSION_CONTROL.md again):")
    result3 = subprocess.run(["python3", "~/fleet/misty/heartbeat_optimize.py"], 
                          capture_output=True, text=True)
    print(f"   Exit code: {result3.returncode}")
    print(f"   Output: {result3.stdout.strip()}")
    
    # Restore MISSION_CONTROL.md
    print("\n5. Restoring MISSION_CONTROL.md...")
    with open(mc_path, "r") as f:
        lines = f.readlines()
    with open(mc_path, "w") as f:
        f.writelines([line for line in lines if not line.startswith("# TEST COMMENT")])
    
    # Fourth run - should skip reading MISSION_CONTROL.md again
    print("\n6. Fourth run (should skip MISSION_CONTROL.md again):")
    result4 = subprocess.run(["python3", "~/fleet/misty/heartbeat_optimize.py"], 
                          capture_output=True, text=True)
    print(f"   Exit code: {result4.returncode}")
    print(f"   Output: {result4.stdout.strip()}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY:")
    # Exit code 0 means "should read", exit code 1 means "should not read"
    print(f"  Run 1 (first): {'PASS' if result1.returncode == 0 else 'FAIL'} (exit {result1.returncode})")
    print(f"  Run 2 (unchanged): {'PASS' if result2.returncode == 1 else 'FAIL'} (exit {result2.returncode})")
    print(f"  Run 3 (modified): {'PASS' if result3.returncode == 0 else 'FAIL'} (exit {result3.returncode})")
    print(f"  Run 4 (restored): {'PASS' if result4.returncode == 1 else 'FAIL'} (exit {result4.returncode})")
    
    all_pass = (result1.returncode == 0 and result2.returncode == 1 and 
                result3.returncode == 0 and result4.returncode == 1)
    print(f"\n  Overall: {'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
    return all_pass

if __name__ == "__main__":
    success = test_optimization()
    exit(0 if success else 1)
