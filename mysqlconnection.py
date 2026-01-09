import pymysql.cursors

class MySQLConnection:
    def __init__(self, db=None):
        self.connection = pymysql.connect(
            host='mysql.railway.internal',  # Railway internal host
            user='root',
            password='srnLtucTexMTNTanvhqbSRKGRMyhBhIW',
            db=db or 'railway',
            port=3306,                      # Railway internal port
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

def connectToMySQL(db=None):
    return MySQLConnection(db)
