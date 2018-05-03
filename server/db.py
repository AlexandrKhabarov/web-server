import sqlite3


class DbBlog:
    def __init__(self, name):
        self.conn = sqlite3.connect(name)
        self.cur = self.conn.cursor()

    def create_table(self):
        self.cur.execute('''
        create table blog_table
            (
                id integer, 
                title integer, 
                content text,
                primary key id autoincrement
            )
            ''')
        self.cur.execute('''
        create table templates
            (
                id integer, 
                name text, 
                template text,
                primary key id autoincrement
            )
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
            where name={name}'''.format(name=name)).fetchall()

    def insert_template(self, name, template):
        self.cur.execute('''insert into templates 
                                values({name}, {template}) '''.format(name=name, template=template))
        self.conn.commit()

    def insert_post(self, title, content):
        self.cur.execute('''insert into blog_table 
                                values({title}, {content}) '''.format(title=title, content=content))
        self.conn.commit()

    def close(self):
        self.conn.close()
