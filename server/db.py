import sqlite3


class DbBlog:
    def __init__(self, name):
        self.conn = sqlite3.connect(name)
        self.cur = self.conn.cursor()

    def truncate_blog_table(self):
        self.cur.execute('''
        delete from blog_table;
        ''')

    def create_tables(self):
        self.cur.execute('''
        create table if not exists blog_table
            (
                id integer primary key autoincrement,
                title text not null, 
                content text not null
            );
            ''')
        self.conn.commit()

    def get_post(self, num_post):
        result = self.cur.execute('''
        select content 
            from blog_table 
            where id = {id}'''.format(id=num_post)).fetchall()
        if result:
            return result[0][0]

    def insert_post(self, title, content):
        self.cur.execute('''insert into blog_table (title, content)
                                values("{title}", "{content}");'''.format(title=title, content=content))
        self.conn.commit()

    def close(self):
        self.cur.close()
        del self.cur
        self.conn.close()
