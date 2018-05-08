from server.server import BlogServer

if __name__ == "__main__":
    server = BlogServer('127.0.0.1', 8889)
    server.start_server()
