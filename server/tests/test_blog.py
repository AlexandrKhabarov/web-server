import unittest
import sqlite3
from server.server import BlogServer
import requests
from multiprocessing import Process
import time


class BlogServerTest(unittest.TestCase):
    address, port = "127.0.0.1", 8889
    server = BlogServer(address, port)

    @classmethod
    def setUpClass(cls):
        cls.server_thread = Process(target=cls.server.start_server)
        cls.cur = sqlite3.connect("blog.db").cursor()
        cls.server_thread.start()
        time.sleep(5)
    # delete numbers
    def test1_main_page(self):
        good_answer = '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <title>Title</title>\n    <link rel="stylesheet" href="/css/styles.css">\n</head>\n<body>\n<div class="container">\n    <h1>Hello to the main page of the blog!</h1>\n    <div>\n        <div>\n            <a href="create-post/">Create POST</a>\n        </div>\n        <div>\n            <a href="1/">Read all Posts</a>\n        </div>\n    </div>\n    <img src="/images/cat.jpg">\n</div>\n</body>\n</html>'
        r = requests.get(
            "http://{}:{}/".format(self.address, self.port),
            headers={"Accept": "application/json"}
        )
        self.assertEqual(good_answer, r.json())

    def test2_create_page(self):
        good_answer = '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <title>Title</title>\n    <link rel="stylesheet" href="/css/styles.css">\n</head>\n<body>\n<div class="container">\n    <div class="form-wrapper">\n        <form method="POST">\n            <div><label for="title">Title:</label><input id="title" name="title" type="text"></div>\n            <div>\n                <button>create_post</button>\n            </div>\n            <div>\n                <label for="post">POST:</label><textarea name="post" id="post" cols="30" rows="10"></textarea>\n            </div>\n        </form>\n    </div>\n    <a href="/">THis is link to the INDex</a>\n</div>\n</body>\n</html>'
        r = requests.get(
            "http://{}:{}/create-post".format(self.address, self.port),
            headers={"Accept": "application/json"}
        )
        self.assertEqual(good_answer, r.json())

    def test3_blog_page_without_content(self):
        good_answer = '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <title>Title</title>\n    <link rel="stylesheet" href="/css/styles.css">\n</head>\n<body>\n    <div class="container">\n        <div class="header">\n            <h1>It is Awesome BLOG!</h1>\n        </div>\n        <div class="create-post">\n            <a href="/create-post/">create post</a>\n        </div>\n        <div class="title">\n            <p>"None"</p>\n        </div>\n        <div class="navigation">\n            <div class="button-next">\n                <a href="/0/">next</a>\n            </div>\n            <div class="button-index"><a href="/">go to the main page</a></div>\n            <div class="button-previous">\n                <a href="/2/">previous</a>\n            </div>\n        </div>\n    </div>\n</body>\n</html>'
        r = requests.get(
            "http://{}:{}/1".format(self.address, self.port),
            headers={"Accept": "application/json"}
        )
        self.assertEqual(good_answer, r.json())

    def test4_create_post(self):
        title, post = "THIS IS TITLE", "THIS IS POST"
        requests.post(
            "http://{}:{}/create-post".format(self.address, self.port),
            data={"title": title, "post": post})
        _, title_db, post_db = self.cur.execute("select * from blog_table").fetchall()[0]
        self.assertEqual(title_db, title)
        self.assertEqual(post_db, post)

    def test5_blog_page_with_created_post(self):
        good_answer = '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <title>Title</title>\n    <link rel="stylesheet" href="/css/styles.css">\n</head>\n<body>\n    <div class="container">\n        <div class="header">\n            <h1>It is Awesome BLOG!</h1>\n        </div>\n        <div class="create-post">\n            <a href="/create-post/">create post</a>\n        </div>\n        <div class="title">\n            <p>"THIS IS POST"</p>\n        </div>\n        <div class="navigation">\n            <div class="button-next">\n                <a href="/0/">next</a>\n            </div>\n            <div class="button-index"><a href="/">go to the main page</a></div>\n            <div class="button-previous">\n                <a href="/2/">previous</a>\n            </div>\n        </div>\n    </div>\n</body>\n</html>'
        r = requests.get(
            "http://{}:{}/1".format(self.address, self.port),
            headers={"Accept": "application/json"}
        )
        self.assertEqual(good_answer, r.json())

    def test6_bad_page(self):
        good_answer = '<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <title>404</title>\n</head>\n<body>\n\n    <h1 align="center">404</h1>\n\n</body>\n</html>'
        r = requests.get(
            "http://{}:{}/12wdfssdfw234".format(self.address, self.port),
            headers={"Accept": "application/json"})
        self.assertEqual(good_answer, r.json())


if __name__ == "__main__":
    unittest.main()
