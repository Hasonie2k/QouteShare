import os
import pymysql.cursors

class MySQLConnection:
    def __init__(self, db=None):
        self.connection = pymysql.connect(
            host=os.getenv('MYSQLHOST', 'nozomi.proxy.rlwy.net'),
            user=os.getenv('MYSQLUSER', 'root'),
            password=os.getenv('MYSQLPASSWORD', 'srnLtucTexMTNTanvhqbSRKGRMyhBhIW'),
            db=os.getenv('MYSQLDATABASE', db or 'railway'),
            port=int(os.getenv('MYSQLPORT', 58910)),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )

    def query_db(self, query: str, data: dict = None):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, data)
                if query.lower().startswith("insert"):
                    return cursor.lastrowid
                elif query.lower().startswith("select"):
                    return cursor.fetchall()
                else:
                    return True
        except Exception as e:
            print("Database query error:", e)
            return False
        # DO NOT close connection here — keep it open per request

def connectToMySQL(db=None):
    return MySQLConnection(db)
