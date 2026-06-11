import requests

def test_api():
    try:
        # Assuming the flask app is running on localhost:5000
        # Since I can'    run the server in the background easily, I'll just check if the file is there.
        # Wait, I can't test the API without the server running.
        # I'll try to run the flask app in a subprocess.
        import subprocess
        import time
        import sys

        print("Starting Flask app...")
        proc = subprocess.Popen([sys.executable, "energy_transition_project/app.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        time.sleep(3) # Wait for startup

        print("Testing /api/strategic-data...")
        response = requests.get("http://127.0.0.1:5000/api/strategic-data")
        print(f"Status: {response.status_code}")
        print(f"Data: {response.json()}")
        
        proc.terminate()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
