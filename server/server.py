import json
import datetime
import socket
import logging
import re
import os
import sys
import abc
from urllib import parse
from server import urls
from server import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HTTP_Server")


class BaseServer(metaclass=abc.ABCMeta):
    SUPPORT_ACCEPTS = [
        "text/html", "application/json", "text/css", "image/png", "image/svg", "image/gif", "image/*", "*/*"
    ]
    HTTP_VERSION = "HTTP/1.1"
    SERVER_NAME = None
    WORK_DIR = None
    STATIC_DIR = None
    TEMPLATE_DIR = None
    TEMPLATE_404_path = None
    URLS = None
    DB = None
    HTTP_TEMPLATE_ANSWER = """{version} {code} {rubric}\nServer: super-server\nDate: {date}\nContent-Type: {content}; charset="utf-8"\nContent-Disposition: inline\nContent-Length: {content_length}\n\n"""

    def __init__(self, address="127.0.0.1", port=8888):
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
                logger.info("server accept connection from {}".format(adr))
                try:
                    self._handle_request(client_sock)
                except Exception:
                    logger.error("connection was aborted {}".format(adr))
                finally:
                    client_sock.close()
        except KeyboardInterrupt:
            logger.info("Server terminate")
            self.socket.close()
            self.DB.close()
            sys.exit(0)

    def _handle_request(self, client_sock):
        data = client_sock.recv(2048)
        response = self._handle_method(data)
        client_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        client_sock.sendall(response)

    def _handle_method(self, request: bytes):
        start_row, headers, body = self._parse_request(request)
        if start_row['method'] == "GET":
            response = self._do_get(start_row, headers, body)
        elif start_row['method'] == "POST":
            response = self._do_post(start_row, headers, body)
        else:
            response = self._do_error(code=405, rubric="Method Not Allowed", type_content=headers.get("accept"))
        return response

    def _parse_request(self, request: bytes):
        request = request.decode('utf-8').replace("\r", "").strip()
        try:
            request_headers, request_body = request.split('\n\n')
            return self._recognize_parameters(
                request_head=request_headers.split('\n'),
                request_body=request_body
            )
        except ValueError:
            return self._recognize_parameters(request_head=request.split("\n"))

    def _recognize_parameters(self, request_head, request_body=None):
        body = {}
        start_row = self._parse_start_row_request(request_head[0])
        headers = self._parse_headers_request(request_head[1:])
        if request_body is not None:
            body = self._parse_body_request(request_body)

        headers["accept"] = self._check_accept_format(headers.get("accept"))

        if start_row['version'] == self.HTTP_VERSION:
            return start_row, headers, body if body else None

    @staticmethod
    def _parse_body_request(request_body):
        body = {}
        for arg in request_body.replace("+", " ").strip().split("&"):
            option, value = arg.split("=")
            body[option] = parse.unquote(value)
        return body

    def _parse_start_row_request(self, request_start_row):
        start_row = {}
        start_row['method'], uri, start_row['version'] = request_start_row.split(" ")
        if uri.find("?") > 0:
            start_row["args"] = {}
            start_row["uri"], start_row["args"] = self._parse_with_arguments(uri)
        else:
            start_row["uri"] = uri

        return start_row

    @staticmethod
    def _parse_with_arguments(uri):
        uri, params = uri.split("?")
        args = {}
        for param in params.split("&"):
            key, val = param.split("=")
            args[key] = val
        return uri, args

    @staticmethod
    def _parse_headers_request(request_headers):
        headers = {}
        for option in request_headers:
            try:
                opt, val = option.split(":", maxsplit=1)
                val = list(map(lambda x: x.strip(), val.split(",")))
                headers[opt.lower()] = val
            except Exception:
                logger.warning("request have wrong header {}".format(option))
        return headers

    def _check_accept_format(self, accept_value):
        if not any(list(map(lambda x: x in self.SUPPORT_ACCEPTS, accept_value))):
            return ["text/html"]
        return accept_value

    @abc.abstractmethod
    def _do_get(self, start_row, headers, body):
        raise NotImplementedError

    @abc.abstractmethod
    def _do_post(self, start_row, headers, body):
        raise NotImplementedError

    @abc.abstractmethod
    def _do_error(self, code, rubric, type_content):
        raise NotImplementedError


class BlogServer(BaseServer):
    SERVER_NAME = "Default Server"
    WORK_DIR = os.path.dirname(os.path.abspath(__file__))
    STATIC_DIR = os.path.join(WORK_DIR, "static")
    TEMPLATE_DIR = os.path.join(WORK_DIR, "template")
    TEMPLATE_404_path = os.path.join(TEMPLATE_DIR, "html-404.html")
    DATABASE_NAME = None
    DB = None
    URLS = urls.urls

    def setup_db(self, db_name):
        self.DATABASE_NAME = os.path.join(self.WORK_DIR, db_name)
        if not os.path.exists(self.DATABASE_NAME):
            self.DB = db.DbBlog(self.DATABASE_NAME)
            self._prepare_db()
        self.DB = db.DbBlog(self.DATABASE_NAME)

    def _prepare_db(self):
        self.DB.create_tables()

    def start_server(self, db_name="blog.db"):
        self.setup_db(db_name)
        super().start_server()

    def _do_get(self, start_row, header, body):
        try:
            html, content = self._validate_uri(start_row.get("uri").strip("/"))
            if html is not None:
                response = self._construct_http_response(
                    code=200,
                    version=start_row["version"],
                    rubric="OK",
                    date=datetime.date.today(),
                    type_content=header['accept'][0],
                    html=html,
                    content=content,
                )
                return response
        except Exception:
            html = self._validate_uri(start_row.get("uri").strip("/"))
            if html is not None:
                response = self._construct_http_response(
                    code=200,
                    version=self.HTTP_VERSION,
                    rubric="OK",
                    date=datetime.date.today(),
                    type_content=header['accept'][0] or None,
                    html=html,
                )
                return response

        return self._do_error(code=404, rubric="Not Found", type_content=header.get("accept"))

    def _do_post(self, start_row, header, body):
        if start_row.get("uri").strip("/") == "create-post":
            template = self._get_template("create-post.html")
            template = bytes(template.format(index="/"), "utf-8")
            if body is not None:
                try:
                    self.DB.insert_post(body.get("title"), body.get("post"))
                    return self._construct_http_response(
                        code=201,
                        version=start_row["version"],
                        rubric="OK",
                        date=datetime.date.today(),
                        type_content=header['accept'][0],
                        html=template
                    )
                except Exception:
                    return self._do_error(code=404, rubric="Not Found", type_content=header.get("accept"))

    def _do_error(self, code=400, rubric="Bad Request", type_content=None):

        with open(self.TEMPLATE_404_path, 'rb') as f:
            return self._construct_http_response(
                code=code,
                version=self.HTTP_VERSION,
                rubric=rubric,
                date=datetime.date.today(),
                type_content=type_content or None,
                html=f.read()
            )

    def _validate_uri(self, uri):
        response = self._search_template(uri)
        if response is not None:
            return response
        response = self._search_static(uri)
        if response is not None:
            return response

    def _search_template(self, uri):
        for path in self.URLS.keys():
            match_uri = re.match(path, uri)
            if match_uri:
                name = self.URLS[path].get("name")
                template = None
                if name == "index.html":
                    template = self._get_template(name)
                    try:
                        template = template.format(
                            create_post="create-post/",
                            read_all_post="1/"
                        )
                    except AttributeError:
                        logger.warning("template with name: {} does not exist".format(name))
                elif name == "create-post.html":
                    template = self._get_template(name)
                    try:
                        template = template.format(index="/")
                    except AttributeError:
                        logger.warning("Template with name: {} does not exist".format(name))
                elif name == "blog-post.html":
                    template = None
                    content = self.DB.get_post(int(match_uri.group()))
                    if content:
                        template = self._get_template(name)
                        try:
                            template = template.format(
                                create_post="/create-post/",
                                index="/",
                                content=content or None,
                                previous_post="/{}/".format(str(int(match_uri.group()) - 1)),
                                next_post="/{}/".format(str(int(match_uri.group()) + 1))
                            )
                            return bytes(template, 'utf-8'), bytes(str(content), 'utf-8')
                        except AttributeError:
                            logger.warning("template with name {} does not exist".format(name))
                if template:
                    return bytes(template, 'utf-8')

    def _get_template(self, name):
        abs_path = os.path.join(self.TEMPLATE_DIR, name)
        if os.path.exists(abs_path):
            with open(os.path.join(self.TEMPLATE_DIR, name)) as f:
                return f.read()

    def _search_static(self, uri):
        abs_path = os.path.join(self.STATIC_DIR, uri)
        if os.path.exists(abs_path):
            with open(abs_path, 'rb') as f:
                return f.read()
        logger.warning("static file with uri - {} does not exist".format(uri))

    def _construct_http_response(self, code, version, rubric, date, type_content, html, content=None):
        if "application/json" in type_content:
            type_content = "application/json"
            if content is not None:
                html = bytes(json.dumps({"result": content.decode("utf-8")}, ensure_ascii=False), 'utf-8')
            else:
                html = bytes(json.dumps({"result": []}), 'utf-8')
        else:
            type_content = type_content[0]
        return self.HTTP_TEMPLATE_ANSWER.format(
            version=version,
            code=code,
            rubric=rubric,
            date=date,
            content=type_content,
            content_length=len(html),
        ).encode() + html
