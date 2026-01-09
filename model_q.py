from mysqlconnection import connectToMySQL
from flask import flash

class Qoute:
    def __init__(self, data):
        self.id = data.get('id')
        self.users_id = data.get('users_id')
        self.name = data.get('name')
        self.comment = data.get('comment')
        self.qoute = data.get('qoute')
        self.post_date = data.get('post_date')
        self.dislikes = data.get('dislikes', 0)
        self.likes = data.get('likes', 0)

    @classmethod
    def get_all(cls):
        query = "SELECT * FROM Qoute ORDER BY post_date DESC;"
        results = connectToMySQL('railway').query_db(query)
        return [cls(q) for q in results] if results else []

    @classmethod
    def get_by_id(cls, quote_id):
        query = "SELECT * FROM Qoute WHERE id=%(id)s;"
        data = {'id': quote_id}
        result = connectToMySQL('railway').query_db(query, data)
        if result:
            return cls(result[0])
        return None

    @classmethod
    def save_quote(cls, data):
        # Always ensure post_date is a string in YYYY-MM-DD format
        if isinstance(data.get('post_date'), str) == False:
            import datetime
            data['post_date'] = datetime.date.today().isoformat()

        query = (
            "INSERT INTO Qoute (name, comment, qoute, users_id, post_date, dislikes, likes) "
            "VALUES (%(name)s, %(comment)s, %(qoute)s, %(users_id)s, %(post_date)s, %(dislikes)s, %(likes)s);"
        )
        new_id = connectToMySQL('railway').query_db(query, data)
        if not new_id:
            flash("Failed to save quote. Please try again.")
        return new_id

    @staticmethod
    def validate_quote(form_data):
        if 'qoute' not in form_data or len(form_data['qoute'].strip()) < 5:
            flash('Quote must be at least 5 characters long.')
            return False
        return True
