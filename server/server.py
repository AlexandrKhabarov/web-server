import json
import datetime
import socket
import logging
import re
import os
import sys
from urllib import parse
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
        request_options = self._parse_request(request) # todo: переименоваит или разбить (header - not title)
        if request_options['method'] == "GET":
            response = self._do_get(request_options)
        elif request_options['method'] == "POST":
            response = self._do_post(request_options)
        else:
            response = self._do_error(code=405, rubric="Method Not Allowed", type_content=request_options.get("accept"))
        return response

    def _parse_request(self, request: bytes):
        request = request.decode('utf-8').replace("\r", "").strip()
        try: # todo (ничего не понятно сделать читабельнее) # args - не body
            request_headers, request_body = request.split('\n\n')
            return self._parse_body(
                chunk_request=request_headers.split('\n'),
                args=request_body
            )
        except ValueError:
            return self._parse_body(chunk_request=request.split("\n"))

    def _parse_body(self, chunk_request, args=None): #todo (переменные для читабельности)
        header = {}
        self._parse_title_request(header, chunk_request[0])
        self._parse_format_of_request(header, chunk_request[1:])
        if args is not None:
            self._parse_args(header, args)
        if header['version'] == self.HTTP_VERSION:
            return header

    @staticmethod
    def _parse_args(header, args): # todo имена
        header["args"] = {}
        for arg in args.replace("+", " ").strip().split("&"):
            option, value = arg.split("=")
            header["args"][option] = parse.unquote(value)

    def _parse_title_request(self, header, content):
        if content.find("?") > 0:
            self._parse_with_arguments(header, content)
        else:
            self._parse_without_arguments(header, content)

    @staticmethod
    def _parse_with_arguments(header, content): # todo парсинг без аргументов включает в себя парсинг с аргументами
        header['method'], opts, header['version'] = content.split(" ")
        header['uri'], opts = opts.split("?")
        header['args'] = {}
        for opt in opts.split("&"):
            key, val = opt.split("=")
            header['args'][key] = val

    @staticmethod
    def _parse_without_arguments(header, content): # todo переименовать и вызвать в верхнем можно
        header['method'], header['uri'], header['version'] = content.split(" ")

    def _parse_format_of_request(self, header, content):
        for option in content:
            try:
                opt, val = option.split(":", maxsplit=1)
                header[opt.lower()] = list(map(lambda x: x.strip(), val.split(","))) # todo либо переменная либо метод (не читается)
            except Exception:
                if header.get("method") == "POST": # todo пересмотреть ексептион
                    header["post"] = {}
                    try:
                        for note in option.strip("&").split("&"):
                            opt, val = note.split("=")
                            header["post"][opt] = val.replace("+", " ")
                    except Exception:
                        pass

        accept_value = header.get("accept", None) # todo отдельный метод назначение дефолтного формата в отдельный меод
        if not any(list(map(lambda x: x in self.SUPPORT_ACCEPTS, accept_value))): # todo если ассепт не поддерживается то ругается
            header["accept"] = ["text/html"]

    def _do_get(self, header): # TODO без реализованных методов сервер не нужен ( использовать abc )
        raise NotImplementedError

    def _do_post(self, header):
        raise NotImplementedError

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

    def setup_db(self, db_name): # todo пересмотреть
        self.DATABASE_NAME = os.path.join(self.WORK_DIR, db_name)
        if not os.path.exists(self.DATABASE_NAME):
            self.DB = db.DbBlog(self.DATABASE_NAME)
            self._prepare_db()
        elif not os.path.isfile(self.DATABASE_NAME): # todo проверка не полная и без неё можно обойтись (ругаться должен sqlite)
            os.rename(self.DATABASE_NAME, self.DATABASE_NAME + ".back")
            self.DB = db.DbBlog(self.DATABASE_NAME)
            self._prepare_db()
        self.DB = db.DbBlog(self.DATABASE_NAME)

    def _prepare_db(self):
        self.DB.create_tables()

    def start_server(self, db_name="blog.db"):
        self.setup_db(db_name)
        super().start_server()

    def _do_get(self, header):
        """Content must be byte array"""
        try:
            html, content = self._validate_uri(header.get("uri").strip("/"))
            if html is not None:
                response = self._construct_http_response(
                    code=200,
                    version=self.HTTP_VERSION,
                    rubric="OK",
                    date=datetime.date.today(),
                    type_content=header['accept'][0] or None,
                    html=html,
                    content=content,
                )
                return response
        except Exception:
            html = self._validate_uri(header.get("uri").strip("/"))
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

    def _do_post(self, header):
        if header.get("uri").strip("/") == "create-post":
            if header.get("args", None) is not None:
                try:
                    self.DB.insert_post(header.get("args").get("title"), header.get("args").get("post"))
                    return self._construct_http_response(
                        code=201,
                        version=self.HTTP_VERSION,
                        rubric="OK",
                        date=datetime.date.today(),
                        type_content=header['accept'][0] or None,
                        html=bytes(self._get_template("create-post.html").format(
                            index="/"
                        ), "utf-8")
                    )
                except Exception as e:
                    print(e)
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
                    template = self._get_template(name)
                    template = template.format(
                        create_post="create-post/",
                        read_all_post="1/"
                    )
                elif name == "create-post.html":
                    template = self._get_template(name)
                    template = template.format(index="/")
                elif name == "blog-post.html":
                    template = self._get_template(name)
                    content = self.DB.get_post(int(match_uri.group()))
                    if content:
                        template = template.format(
                            create_post="/create-post/",
                            index="/",
                            content=content or None,
                            previous_post="/{}/".format(str(int(match_uri.group()) - 1)),
                            next_post="/{}/".format(str(int(match_uri.group()) + 1))
                        )
                        return bytes(template, 'utf-8'), bytes(str(content), 'utf-8')
                    else:
                        return None
                return bytes(template, 'utf-8')

    def _get_template(self, name): # todo проверить путь на диске не кидать исключение в предыдущем методе завалиься на байтах
        try:
            with open(os.path.join(self.TEMPLATE_DIR, name)) as f:
                return f.read()
        except Exception: # todo pep20 ошибки не должны замалчиваться, если html не существует кидаем ошибку на верх
            pass # todo выкинуть трай эксепт

    def _search_static(self, uri, static): # todo просто чекнуть есть или нет статика в папке os.path.exists().
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

    def _construct_http_response(self, code, version, rubric, date, type_content, html, content=None):
        if "application/json" in type_content:
            if content is not None:
                html = bytes(json.dumps({"html": content.decode("utf-8")}), 'utf-8')
            else:
                html = bytes(json.dumps({"html": []}), 'utf-8') # todo [] - валидная структура в json не обязателен ключ (results можно переименовать)
        return self.HTTP_TEMPLATE_ANSWER.format(
            version=version,
            code=code,
            rubric=rubric,
            date=date,
            content=type_content[0] or "text/html", # todo уже обрабатывал
            content_length=len(html),
        ).encode() + html
