import datetime
import socket
import logging
import re
import os
from server import urls
from server import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HTTP_Server")


class BaseServer:
    SUPPORT_ACCEPTS = ["text/html", "application/json", "text/css", "image/png", "image/svg", "image/gif", "image/*",
                       "*/*"]
    HTTP_VERSION = "HTTP/1.1"
    SERVER_NAME = None
    WORK_DIR = None
    STATIC_DIR = None
    TEMPLATE_DIR = None
    TEMPLATE_404_path = None
    URLS = None
    DB = None
    HTTP_TEMPLATE_ANSWER = """{version} {code} {rubric}
    Server: super-server
    Date: {date}
    Content-Type: {content}
    Content-Length: {content_length}\n
    """

    # {body}

    def __init__(self, address="127.0.0.1", port=8888):
        self.address = address
        self.port = port
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            # proto=0
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
        """ Header is dict. This dict has keys. Keys is options of request body.
            Methods _do_get, _do_post, _do_error must return bytes.
        """
        header = self._parse_request(request)
        if header['method'] == "GET":
            response = self._do_get(header)
        elif header['method'] == "POST":
            response = self._do_post(header)
        else:
            response = self._do_error(code=405, rubric="Method Not Allowed")
        return response

    def _parse_request(self, request: bytes):
        try:
            chunk_request, args = request.decode('utf-8').replace("\r", "").strip().split('\n\n')
            return self._parse_body(chunk_request=chunk_request, args=args)
        except ValueError:
            chunk_request = request.decode('utf-8').replace("\r", "").strip().split("\n")
            return self._parse_body(chunk_request=chunk_request)

    def _parse_body(self, chunk_request, args=None):
        header = {}
        self._parse_title_request(header, chunk_request[0])
        self._parse_format_of_request(header, chunk_request[1:])
        if args is not None:
            self._parse_args(header, args)
        if header['version'] == self.HTTP_VERSION:
            return header

    @staticmethod
    def _parse_args(header, args):
        for arg in args.replace("+", " ").strip().split("&"):
            option, value = arg.split("=")
            header["args"] = {}
            header["args"][option] = value

    def _parse_title_request(self, header, content):
        if content.find("?") > 0:
            self._parse_with_arguments(header, content)
        else:
            self._parse_without_arguments(header, content)

    @staticmethod
    def _parse_with_arguments(header, content):
        header['method'], opts, header['version'] = content.split(" ")
        header['uri'], opts = opts.split("?")
        header['args'] = {}
        for opt in opts.split("&"):
            key, val = opt.split("=")
            header['args'][key] = val

    @staticmethod
    def _parse_without_arguments(header, content):
        header['method'], header['uri'], header['version'] = content.split(" ")

    def _parse_format_of_request(self, header, content):
        for option in content:
            opt, val = option.split(":", maxsplit=1)
            header[opt.lower()] = list(map(lambda x: x.strip(), val.split(",")))
        accept_value = header.get("accept", None)
        if not any(list(map(lambda x: x in self.SUPPORT_ACCEPTS, accept_value))):
            header["accept"] = "text/html"

    def _do_get(self, header):
        raise NotImplementedError

    def _do_post(self, header):
        raise NotImplementedError

    def _do_error(self, code, rubric):
        raise NotImplementedError


class BlogServer(BaseServer):
    SERVER_NAME = "Default Server"
    WORK_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(WORK_DIR, "static")
    TEMPLATE_DIR = os.path.join(WORK_DIR, "template")
    TEMPLATE_404_path = os.path.join(TEMPLATE_DIR, "html-404.html")
    DB = db.DbBlog("blog.db")
    URLS = urls.urls

    def setup_db(self):
        self.DB.create_tables()
        for root, _, templates in os.walk(self.TEMPLATE_DIR):
            for template in templates:
                with open(os.path.join(root, template), 'r') as f:
                    self.DB.insert_template(template, f.read())

    def start_server(self):
        self.setup_db()
        super().start_server()

    def _do_get(self, header):
        """Content must be byte array"""
        content = self._validate_uri(header.get("uri").strip("/"))
        if content is not None:
            response = self._construct_http_response(
                code=200,
                version=self.HTTP_VERSION,
                rubric="OK",
                date=datetime.date.today(),
                type_content=header['accept'][0] or None,
                content=content
            )
            return response
        return self._do_error(code=404, rubric="Not Found")

    def _do_post(self, header):
        content = self._validate_uri(header.get("uri"))
        if content:
            response = self._construct_http_response(
                code=200,
                version=self.HTTP_VERSION,
                rubric="OK",
                date=datetime.date.today(),
                type_content=header['accept'][0] or None,
                content=content
            )
            return response
        return self._do_error(code=404, rubric="Not Found")

    def _do_error(self, code=400, rubric="Bad Request", type_content=None):

        with open(self.TEMPLATE_404_path, 'rb') as f:
            return self._construct_http_response(
                code=code,
                version=self.HTTP_VERSION,
                rubric=rubric,
                date=datetime.date.today(),
                type_content=type_content or None,
                content=f.read()
            )

    def _validate_uri(self, uri):
        response = self._search_template(uri)
        if response is not None:
            return response
        response = self._search_static(uri, self.STATIC_DIR)
        if response is not None:
            return response

    def _search_template(self, uri):
        for path in self.URLS.keys():
            match_uri = re.match(path, uri)
            if match_uri:
                name = self.URLS[path].get("name")
                template = None
                if name == "index.html":
                    template = self.DB.get_template(name)
                    template = template[0][0].format(
                        create_post="create-post/",
                        read_all_post="1/"
                    )
                elif name == "create-post.html":
                    template = self.DB.get_template(name)
                    template = template[0][0].format(index="/")
                elif name == "blog-post.html":
                    template = self.DB.get_template(name)
                    template = template[0][0].format(
                        create_post="create_post/",
                        content=self.DB.get_post(name),
                        previous_post=self.DB.get_post(name - 1),
                        next_post=self.DB.get_post(name + 1)
                    )
                return bytes(template, 'utf-8')

    def _search_static(self, uri, static):
        abs_path = os.path.join(self.STATIC_DIR, uri)
        dir_name = os.path.dirname(abs_path)
        static_name = os.path.basename(abs_path)
        for root, dirs, static_files in os.walk(static):
            if dir_name == root:
                for static_file in static_files:
                    if static_name == static_file:
                        with open(os.path.join(root, static_file), 'rb') as f:
                            content = f.read()
                        return content
            for dir in dirs:
                static_file = self._search_static(uri, os.path.join(root, dir))
                if static_file is not None:
                    return static_file

    def _construct_http_response(self, code, version, rubric, date, type_content, content):
        return self.HTTP_TEMPLATE_ANSWER.format(
            version=version,
            code=code,
            rubric=rubric,
            date=date,
            content=type_content or "text/html",
            content_length=len(content),
            # body=content.decode('utf-8')
        ).encode() + content
