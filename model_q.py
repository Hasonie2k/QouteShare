from mysqlconnection import connectToMySQL
from flask import flash

class Qoute:
    def __init__(self, data):
        self.id = data['id']
        self.name = data['name']
        self.qoute = data['qoute']
        self.comment = data.get('comment', '')
        self.users_id = data['users_id']
        self.post_date = data['post_date']
        self.likes = data.get('likes', 0)
        self.dislikes = data.get('dislikes', 0)

    @classmethod
    def get_all(cls):
        query = "SELECT * FROM qoute ORDER BY post_date DESC;"
        results = connectToMySQL('railway').query_db(query)
        return [cls(quote) for quote in results] if results else []

    @classmethod
    def get_by_id(cls, quote_id):
        query = "SELECT * FROM qoute WHERE id = %(quote_id)s;"
        data = {'quote_id': quote_id}
        result = connectToMySQL('railway').query_db(query, data)
        return cls(result[0]) if result and len(result) > 0 else None

    @classmethod
    def get_by_name(cls, name):
        query = "SELECT * FROM qoute WHERE name = %(name)s;"
        data = {'name': name}
        result = connectToMySQL('railway').query_db(query, data)
        return cls(result[0]) if result and len(result) > 0 else None

    @classmethod
    def save_quote(cls, data):
        query = (
            "INSERT INTO qoute (name, comment, qoute, users_id, post_date, likes, dislikes) "
            "VALUES (%(name)s, %(comment)s, %(qoute)s, %(users_id)s, %(post_date)s, %(likes)s, %(dislikes)s);"
        )
        new_id = connectToMySQL('railway').query_db(query, data)
        return new_id

    @classmethod
    def update_quote_by_id(cls, data):
        query = (
            "UPDATE qoute SET name=%(name)s, comment=%(comment)s, qoute=%(qoute)s, "
            "users_id=%(users_id)s, post_date=%(post_date)s, likes=%(likes)s, dislikes=%(dislikes)s "
            "WHERE id=%(id)s;"
        )
        print('DEBUG: update_quote_by_id called with:')
        print('Query:', query)
        print('Data:', data)
        result = connectToMySQL('railway').query_db(query, data)
        print('Result:', result)
        return result

    @classmethod
    def delete_quote_by_id(cls, quote_id):
        query = "DELETE FROM qoute WHERE id=%(quote_id)s;"
        data = {'quote_id': quote_id}
        return connectToMySQL('railway').query_db(query, data)

    @staticmethod
    def validate_quote(form_data):
        is_valid = True
        if not form_data.get('qoute') or len(form_data['qoute'].strip()) < 1:
            flash('Quote cannot be empty.')
            is_valid = False
        return is_valid
