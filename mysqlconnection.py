import os
import pymysql.cursors

class MySQLConnection:
    def __init__(self, db=None):
        # Use Railway's environment variables
        connection = pymysql.connect(
            host=os.getenv('MYSQLHOST', 'localhost'),
            user=os.getenv('MYSQLUSER', 'root'),
            password=os.getenv('MYSQLPASSWORD', ''),
            db=os.getenv('MYSQLDATABASE', db),
            port=int(os.getenv('MYSQLPORT', 3306)),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        self.connection = connection

    def query_db(self, query: str, data: dict = None):
        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, data)
                if query.lower().startswith("insert"):
                    return cursor.lastrowid
                elif query.lower().startswith("select"):
                    return cursor.fetchall()
                else:
                    return True
            except Exception as e:
                print("Something went wrong:", e)
                return False
            finally:
                self.connection.close()

def connectToMySQL(db=None):
    return MySQLConnection(db)
