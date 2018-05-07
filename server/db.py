import sqlite3


class DbBlog:
    def __init__(self, name):
        self.conn = sqlite3.connect(name)
        self.cur = self.conn.cursor()

    def drop_blog_table(self):
        self.cur.execute('''
        drop table if exists blog_table;
        ''')

    def drop_templates_table(self):
        self.cur.execute('''
        drop table if exists templates;
        ''')

    def create_tables(self):
        self.drop_blog_table()
        self.drop_templates_table()
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
        result = self.cur.execute('''
        select content 
            from blog_table 
            where id = {id}'''.format(id=num_post)).fetchall()
        if result:
            return result[0][0]


    def get_template(self, name):
        result = self.cur.execute('''
        select template 
            from templates 
            where name="{name}";'''.format(name=name)).fetchall()
        if result:
            return result[0][0]


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
