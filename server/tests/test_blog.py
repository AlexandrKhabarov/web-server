import unittest
from server.server import BlogServer
import requests
from multiprocessing import Process
import time
import os
import signal


class BlogServerTest(unittest.TestCase):
    address, port = "127.0.0.1", 8882
    server = BlogServer(address, port)
    test_db = os.path.join(server.WORK_DIR, "test_db.db")

    @classmethod
    def setUpClass(cls):
        cls.server_process = Process(target=cls.server.start_server, args={cls.test_db})
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
        good_answer = 404
        r = requests.get(
            "http://{}:{}/2".format(self.address, self.port),
            headers={"Accept": "application/json"}
        )
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
        os.remove(cls.test_db)
        os.kill(cls.server_process.pid, signal.SIGINT)
        # sys.exit()  sys.exit завалит всё если много тестов


if __name__ == "__main__":
    unittest.main()
