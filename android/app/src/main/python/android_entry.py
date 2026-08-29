import json
import sys
import threading
import time
import urllib.request

_lock = threading.Lock()
_thread = None
_port = 8787


def start_server(root, port=8787):
    global _thread, _port
    root = str(root)
    if root not in sys.path:
        sys.path.insert(0, root)
    from offline.server import serve
    _port = int(port)
    with _lock:
        if _thread is None or not _thread.is_alive():
            _thread = threading.Thread(
                target=serve,
                args=(root, "127.0.0.1", _port),
                name="SolidStateOfflineHTTP",
                daemon=True,
            )
            _thread.start()
    url = f"http://127.0.0.1:{_port}/api/status"
    last = None
    for _ in range(80):
        try:
            with urllib.request.urlopen(url, timeout=0.25) as response:
                data = json.loads(response.read().decode("utf-8"))
            return json.dumps({"status": "READY", "url": f"http://127.0.0.1:{_port}/", "runtime": data})
        except Exception as exc:
            last = type(exc).__name__
            time.sleep(0.05)
    return json.dumps({"status": "FAIL_CLOSED", "code": "LOCAL_SERVER_NOT_READY", "detail": last})
