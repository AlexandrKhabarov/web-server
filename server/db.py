import sqlite3


class DbBlog:
    def __init__(self, name):
        self.conn = sqlite3.connect(name)
        self.cur = self.conn.cursor()

    def create_tables(self):
        self.cur.execute('''
        create table if not exists blog_table
            (
                id integer primary key autoincrement,
                title text not null, 
                content text not null
            );
            ''')
        self.cur.execute('''
        create table if not exists templates
            (
                id integer primary key autoincrement, 
                name text not null, 
                template text not null
            );
            ''')

    def get_post(self, num_post):
        return self.cur.execute('''
        select content 
            from blog_table 
            where id = {id}'''.format(id=num_post)).fetchall()

    def get_template(self, name):
        return self.cur.execute('''
        select template 
            from templates 
            where name="{name}";'''.format(name=name)).fetchall()

    def insert_template(self, name, template):
        self.cur.execute('''insert into templates (name, template)
                                values('{name}', '{template}');'''.format(name=name, template=template))
        self.conn.commit()

    def insert_post(self, title, content):
        self.cur.execute('''insert into blog_table (title, content)
                                values("{title}", "{content}");'''.format(title=title, content=content))
        self.conn.commit()

    def close(self):
        self.conn.close()
