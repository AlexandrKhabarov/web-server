urls = {
    "^$": {"template": "index.html", "name": "index.html"},
    "^create-post$": {"template": "create-post.html", "name": "create-post.html"},
    "^[0-9]{1,}$": {"template": "blog-post.html", "name": "blog-post.html"}
}
