import unittest
import sqlite3
from server.server import BlogServer
import requests
from multiprocessing import Process
import time
import os
import sys
import signal


class BlogServerTest(unittest.TestCase):
    address, port = "127.0.0.1", 8888
    server = BlogServer(address, port)

    @classmethod
    def setUpClass(cls):
        cls.server_process = Process(target=cls.server.start_server)
        cls.cur = sqlite3.connect("blog.db").cursor()
        cls.server_process.start()
        time.sleep(5)

    def test_main_page(self):
        good_answer = 200
        r = requests.get(
            "http://{}:{}/".format(self.address, self.port),
            headers={"Accept": "application/json"}
        )
        self.assertEqual(good_answer, r.status_code)

    def test_create_page(self):
        good_answer = 200
        r = requests.get(
            "http://{}:{}/create-post".format(self.address, self.port),
            headers={"Accept": "application/json"}
        )
        self.assertEqual(good_answer, r.status_code)

    def test_blog_page_without_content(self):
        good_answer = 200
        r = requests.get(
            "http://{}:{}/1".format(self.address, self.port),
            headers={"Accept": "application/json"}
        )
        self.assertEqual(good_answer, r.status_code)

    def test_create_post(self):
        title, post = "THIS IS TITLE", "THIS IS POST"
        good_answer = 201
        r = requests.post(
            "http://{}:{}/create-post".format(self.address, self.port),
            data={"title": title, "post": post})
        _, title_db, post_db = self.cur.execute('select * from blog_table where title="{title}"'.format(
            title=title
        )).fetchall()[0]
        self.assertEqual(title_db, title)
        self.assertEqual(post_db, post)
        self.assertEqual(good_answer, r.status_code)

    def test_blog_page_with_created_post(self):
        good_answer = 200
        title, post = "CAT", "DOG"
        requests.post(
            "http://{}:{}/create-post".format(self.address, self.port),
            data={"title": title, "post": post})
        r = requests.get(
            "http://{}:{}/1".format(self.address, self.port),
            headers={"Accept": "application/json"}
        )
        self.assertEqual(post, r.json()['html'])
        self.assertEqual(good_answer, r.status_code)

    def test_bad_page(self):
        good_answer = 404
        r = requests.get(
            "http://{}:{}/12wdfssdfw234".format(self.address, self.port),
            headers={"Accept": "application/json"})
        self.assertEqual(good_answer, r.status_code)

    @classmethod
    def tearDownClass(cls):
        os.remove("./blog.db")
        os.kill(cls.server_process.pid, signal.SIGTERM)
        sys.exit()


if __name__ == "__main__":
    unittest.main()
