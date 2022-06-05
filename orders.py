import sqlite3


class Order(object):
    def __init__(self,
                 userid: int,
                 appname: str = None,
                 appid: int = None,
                 appicon: bytes = None,
                 status: str = None):
        self.userid = userid
        self.appname = appname
        self.appid = appid
        self.appicon = appicon
        self.status = status

    def __repr__(self):
        return f'Order(####{str(self.userid)[-3:]},' \
               f' {self.appname}, {self.appid})'

    def execute(self):
        raise NotImplementedError


class OrdersQueue(object):

    def __init__(self, dbfile) -> None:
        super().__init__()
        self.dbfile = dbfile
        try:
            self.create_orders_table()
        except sqlite3.Error:
            pass

    def init_connection(self):
        return sqlite3.connect(self.dbfile)

    def create_orders_table(self):
        with self.init_connection() as con:
            cur = con.cursor()
            cur.execute("""create table orders (
                    userid integer,
                    appname text,
                    appid integer,
                    appicon blob,
                    status text
                    )""")
        con.close()

    def record_user(self, userid):
        with self.init_connection() as con:
            cur = con.cursor()
            cur.execute("insert into orders (userid) values (?)", (userid, ))
        con.close()

    def update_order(self, order):
        userid = order.userid
        if userid not in self.get_users():
            raise ValueError(f"User #{userid} is not found")

        with self.init_connection() as con:
            cur = con.cursor()
            cur.execute("""
            update orders
            set appname = :appname, appid = :appid, appicon = :appicon, status = :status
            where userid = :userid
            """, {
                'userid': userid,
                'appname': order.appname,
                'appid': order.appid,
                'appicon': order.appicon,
                'status': order.status
            })
        con.close()

    def remove_order(self, userid):
        with self.init_connection() as con:
            cur = con.cursor()
            cur.execute("delete from orders where userid = ?", (userid,))
        con.close()

    def get_order(self, userid):
        with self.init_connection() as con:
            cur = con.cursor()
            cur.execute('select * from orders where userid = ?', (userid,))
            record = cur.fetchone()
        con.close()
        return Order(*record)

    def get_orders(self, status='any'):
        for userid in self.get_users():
            order = self.get_order(userid)
            if status != 'any':
                if order.status == status:
                    yield order
            else:
                yield order

    def get_users(self):
        with self.init_connection() as con:
            cur = con.cursor()
            cur.execute('select userid from orders')
            users = cur.fetchall()
        con.close()
        for user, in users:
            yield user
