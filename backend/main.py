import threading
import time
import webbrowser
from app.api import create_app

def run_api():
    app = create_app()
    app.run(host='127.0.0.1', port=5001, debug=False)

if __name__ == '__main__':
    t = threading.Thread(target=run_api, daemon=True)
    t.start()
    time.sleep(1)
    webbrowser.open('http://localhost:5173/')
    t.join()
