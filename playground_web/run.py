#!/usr/bin/env python3
"""
PepperPy Playground Runner
A script to run the PepperPy Playground with improved hot reload.
"""

import os
import signal
import subprocess
import sys
import time

def kill_previous_instances():
    """Kill any previously running instances of the app."""
    try:
        # Find running processes
        result = subprocess.run(
            ["pgrep", "-f", "python.*app.py"], 
            capture_output=True, 
            text=True
        )
        pids = result.stdout.strip().split('\n')
        
        # Kill processes
        for pid in pids:
            if pid and pid.isdigit() and int(pid) != os.getpid():
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"Terminated previous instance (PID: {pid})")
                except ProcessLookupError:
                    # Process already gone
                    pass
    except Exception as e:
        print(f"Error cleaning up processes: {e}")

def run_app():
    """Run the Flask app with improved hot reload."""
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # The key is to use subprocess directly
    try:
        # Use a custom port if specified
        port = sys.argv[1] if len(sys.argv) > 1 else '5000'
        subprocess.run(
            ["python", "app.py", "--port", port, "--host", "0.0.0.0"], 
            check=True
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
    except subprocess.CalledProcessError as e:
        print(f"Application exited with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    # Kill any existing instances
    kill_previous_instances()
    
    # Small delay to ensure ports are freed
    time.sleep(0.5)
    
    # Run the app
    sys.exit(run_app()) 