import socket
import logging
import os
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HTTP_Server")


class Server:
    SUPPORT_METHODS = ["GET", "POST"]
    SUPPORT_ACCEPTS = ["text/html", "application/json"]
    HTTP_VERSION = "1.1"
    SERVER_NAME = "Server"
    WORK_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(WORK_DIR, "static")
    TEMPLATE_404_path = os.path.join(STATIC_DIR, "html_404.html")
    HTTP_TEMPLATE_ANSWER = """
    HTTP/{version} {code} {rubric}
    Server: super-server
    Date: {date}
    Content-Type: {content}
    Content-Length: {content_length}\n\n
    {body}
    """

    def __init__(self, address, port=8888):
        self.address = address
        self.port = port
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            proto=0
        )

    def start_server(self):
        logger.info("server start")
        self.socket.bind((self.address, self.port))
        self.socket.listen()
        try:
            while True:
                client_sock, adr = self.socket.accept()
                logger.info("server accept connection from {} {}".format(client_sock, adr))
                self._handle_request(client_sock)
        except KeyboardInterrupt:
            logger.info("Server terminate")
            self.socket.close()

    def _handle_request(self, client_sock):
        data = client_sock.recv(1024)
        response = self._handle_method(data)
        client_sock.sendall(response)
        client_sock.close()

    def _handle_method(self, request: bytes):
        header, body, = self._parse_request(request)
        if header['method'] == "GET":
            response = self._do_get(header['uri'])
        elif header['method'] == "POST":
            response = self._do_post(header['uri'], body)
        else:
            response = self._do_error(code=405, rubric="Method Not Allowed")
        return response

    def _parse_request(self, request: bytes):
        chunk_request = request.decode('utf-8').split('\n')
        header = dict()
        self._parse_title_response(header, chunk_request[0])
        if header['version'].split('/')[1].strip('\r') == self.HTTP_VERSION:
            return header, chunk_request[1:]

    def _do_get(self, uri):
        path = self._validate_uri(uri)
        if path:
            response = self._construct_response(path, code=200, rubric="OK")
            return response
        return self._do_error(code=404, rubric="Not Found")

    def _do_post(self, uri, body):
        path = self._validate_uri(uri)
        if path:
            response = self._construct_response(path, code=200, rubric="OK")
            return response
        return self._do_error(code=404, rubric="Not Found")

    def _validate_uri(self, path):
        path = os.path.join(self.STATIC_DIR, path.strip('/'))
        if os.path.exists(path) and os.access(path, os.R_OK):
            return path

    def _do_error(self, code=400, rubric="Bad Request"):
        return self._construct_response(
            self.TEMPLATE_404_path,
            code,
            rubric
        )

    def _construct_response(self, path, code, rubric):
        content = b''
        with open(path, 'rb') as f:
            content += self._construct_http_response(
                code,
                self.HTTP_VERSION,
                rubric,
                datetime.date.today(),
                f.read()
            )
        return content

    def _construct_http_response(self, code, version, rubric, date, content):
        return self.HTTP_TEMPLATE_ANSWER.format(
            version=version,
            code=code,
            rubric=rubric,
            date=date,
            content=content,
            content_length=len(content),
            body=content.decode('utf-8')
        ).encode()

    def _parse_title_response(self, header, content):
        if content.find("?") > 0:
            self._parse_with_arguments(header, content)
        else:
            self._parse_without_arguments(header, content)

    @staticmethod
    def _parse_with_arguments(header, content):
        header['method'], opts, header['version'] = content.strip("\n\t\r").split(" ")
        header['uri'], opts = opts.split("?")
        header['args'] = {}
        for opt in opts.strip("\n\r\t").split("&"):
            key, val = opt.split("=")
            header['args'][key] = val

    @staticmethod
    def _parse_without_arguments(header, content):
        header['method'], header['uri'], header['version'] = content.split(" ")
