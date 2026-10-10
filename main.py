import json
import mimetypes
import pathlib
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

from jinja2 import Environment, FileSystemLoader

DATA_LOG_FILE = pathlib.Path(__file__).resolve().parent / "storage" / "data.json"

env = Environment(loader=FileSystemLoader("."))


class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        pr_url = urllib.parse.urlparse(self.path)

        if pr_url.path == "/message":
            data = self.rfile.read(int(self.headers["Content-Length"]))
            data_parse = urllib.parse.unquote_plus(data.decode())
            data_dict = {
                key: value
                for key, value in [el.split("=") for el in data_parse.split("&")]
            }

            self.save_message(data_dict)

            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
        else:
            self.send_html_file("error.html", 404)

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        elif pr_url.path == "/read":
            self.send_read_page("read.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())

    def send_read_page(self, filename):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        with open(DATA_LOG_FILE, "r") as f:
            messages = json.load(f)

        template = env.get_template("read.html")
        self.wfile.write(template.render(messages=messages).encode())

    def save_message(self, data_dict):
        with open(DATA_LOG_FILE, "r") as f:
            messages = json.load(f)

        timestamp = datetime.now().isoformat(sep=" ", timespec="microseconds")

        messages[timestamp] = {
            "username": data_dict["username"],
            "message": data_dict["message"],
        }

        with open(DATA_LOG_FILE, "w") as f:
            f.write(json.dumps(messages, indent=4))


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
