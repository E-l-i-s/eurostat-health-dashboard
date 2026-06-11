import subprocess
import time
import sys

def run_and_test():
    print("Starting Flask app...")
    proc = subprocess.Popen([sys.executable, "energy_transition_project/app.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(5) # Wait for startup

    import requests
    try:
        print("Testing /api/strategic-data...")
        response = requests.get("http://127.0.0.1:5000/api/strategic-data")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"API Request Error: {e}")

    print("Fetching stderr from Flask...")
    stderr = proc.stderr.read()
    print(f"Flask Error Log:\n{stderr}")
    
    proc.terminate()

if __name__ == "__main__":
    run_and_test()
