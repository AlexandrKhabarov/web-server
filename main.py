from server import Server
import os


class SetupServer:
    PORT = 8888
    ADDRESS = "127.0.0.1"
    SERVER_NAME = "Super_Web_Server"
    WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(WORKING_DIR, "static")
    TEMPLATE_DIR = os.path.join(STATIC_DIR, "templates")
    JS_DIR = os.path.join(STATIC_DIR, "js")
    CSS_DIR = os.path.join(STATIC_DIR, "css")


if __name__ == "__main__":
    server = Server('127.0.0.1', 8889)
    server.start_server()
