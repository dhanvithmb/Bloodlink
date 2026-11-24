"""Run BloodLink locally with: python server.py"""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import json

from model import DONORS, recommend_donors

ROOT = Path(__file__).resolve().parent


class BloodLinkHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        request = urlsplit(self.path)
        if request.path == "/api/donors":
            query = parse_qs(request.query)
            payload = {
                "model": "weighted-k-nearest-neighbors",
                "demo": True,
                "total": len(DONORS),
                "available": sum(donor["available"] for donor in DONORS),
                "cities": sorted({donor["city"] for donor in DONORS}),
                "groups": [
                    {
                        "group": group,
                        "total": sum(donor["group"] == group for donor in DONORS),
                        "available": sum(donor["group"] == group and donor["available"] for donor in DONORS),
                    }
                    for group in ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")
                ],
                "donors": recommend_donors(
                    query.get("group", ["all"])[0],
                    query.get("city", ["all"])[0],
                ),
            }
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if request.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return
        self.path = request.path
        super().do_GET()


if __name__ == "__main__":
    address = ("127.0.0.1", 8000)
    print(f"BloodLink is running at http://{address[0]}:{address[1]}")
    ThreadingHTTPServer(address, BloodLinkHandler).serve_forever()
