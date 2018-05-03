from server import Server
import os

if __name__ == "__main__":
    server = Server('127.0.0.1', 8888)
    server.start_server()
