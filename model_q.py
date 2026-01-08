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
        query = "SELECT * FROM qouteschema.Qoute;"
        results = connectToMySQL('qouteschema').query_db(query)
        qoutes = []
        if results:
            for q in results:
                qoutes.append(cls(q))
        return qoutes

    @classmethod
    def get_by_name(cls, name):
        query = "SELECT * FROM qouteschema.Qoute WHERE name = %(name)s;"
        data = {'name': name}
        result = connectToMySQL('qouteschema').query_db(query, data)
        if result and len(result) > 0:
            return cls(result[0])
        return None

    @classmethod
    def get_by_id(cls, quote_id):
        query = "SELECT * FROM qouteschema.Qoute WHERE id = %(id)s;"
        data = {'id': quote_id}
        result = connectToMySQL('qouteschema').query_db(query, data)
        if result and len(result) > 0:
            return cls(result[0])
        return None

    @classmethod
    def save_quote(cls, data):
        query = (
            "INSERT INTO qouteschema.Qoute (name, comment, qoute, users_id, post_date, dislikes, likes) "
            "VALUES (%(name)s, %(comment)s, %(qoute)s, %(users_id)s, %(post_date)s, %(dislikes)s, %(likes)s);"
        )
        return connectToMySQL('qouteschema').query_db(query, data)

    @classmethod
    def delete_quote_by_id(cls, quote_id):
        query = "DELETE FROM qouteschema.Qoute WHERE id = %(id)s;"
        data = {'id': quote_id}
        return connectToMySQL('qouteschema').query_db(query, data)

    @classmethod
    def update_quote_by_id(cls, data):
        # Only update provided fields, fallback to current values for missing ones
        quote = cls.get_by_id(data['id'])
        if not quote:
            return None
        update_data = {
            'id': data['id'],
            'name': data.get('name', quote.name),
            'comment': data.get('comment', quote.comment),
            'qoute': data.get('qoute', quote.qoute),
            'post_date': data.get('post_date', quote.post_date),
            'dislikes': data.get('dislikes', quote.dislikes),
            'likes': data.get('likes', quote.likes)
        }
        query = (
            "UPDATE qouteschema.Qoute SET name=%(name)s, comment=%(comment)s, qoute=%(qoute)s, "
            "post_date=%(post_date)s, dislikes=%(dislikes)s, likes=%(likes)s WHERE id=%(id)s;"
        )
        return connectToMySQL('qouteschema').query_db(query, update_data)


    @staticmethod
    def validate_quote(form_data):
        is_valid = True
        # Name is now set from the user, not the form, so skip name validation
        # Comment is not required on quote creation
        if 'qoute' not in form_data or len(form_data['qoute']) < 5:
            flash('Quote must be at least 5 characters long.')
            is_valid = False
        return is_valid

    