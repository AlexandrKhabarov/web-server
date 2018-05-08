from server.server import BlogServer

if __name__ == "__main__":
    server = BlogServer('127.0.0.1', 8888)
    server.start_server()
