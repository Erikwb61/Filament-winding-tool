import sys
import traceback

print("Step 1: Importing Flask...")
try:
    from flask import Flask
    print("  OK Flask OK")
except Exception as e:
    print(f"  ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

print("Step 2: Importing fw_core modules...")
try:
    from fw_core.lamina_properties import LaminaDatabase
    from fw_core.laminate_properties import LaminateProperties
    from fw_core.failure_analysis import LaminateFailureAnalysis
    from fw_core.tolerance_analysis import ToleranceAnalysis
    print("  OK All fw_core modules OK")
except Exception as e:
    print(f"  ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

print("Step 3: Importing server...")
try:
    import server
    print("  OK Server module OK")
except Exception as e:
    print(f"  ERROR: {e}")
    traceback.print_exc()
    sys.exit(1)

print("Step 4: Checking if server runs...")
print("  (Server should be running on port 5000)")
print("  Press Ctrl+C to stop")
print("")
try:
    server.app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
except Exception as e:
    print(f"✗ Error starting server: {e}")
    traceback.print_exc()
    sys.exit(1)
