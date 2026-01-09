from mysqlconnection import connectToMySQL

class Comment:
    def __init__(self, data):
        self.id = data['id']
        self.quote_id = data['quote_id']
        self.user_id = data['user_id']
        self.author = data['author']
        self.text = data['text']
        self.date = data['date']
        self.edited = data.get('edited', False)
        self.likes = data.get('likes', 0)
        self.dislikes = data.get('dislikes', 0)

    @classmethod
    def get_by_quote_id(cls, quote_id):
        query = "SELECT * FROM comments WHERE quote_id=%(quote_id)s ORDER BY id ASC;"
        data = {'quote_id': quote_id}
        results = connectToMySQL('railway').query_db(query, data)
        return [cls(comment) for comment in results] if results else []

    @classmethod
    def add_comment(cls, data):
        query = (
            "INSERT INTO comments (quote_id, user_id, author, text, date, edited, likes, dislikes) "
            "VALUES (%(quote_id)s, %(user_id)s, %(author)s, %(text)s, %(date)s, %(edited)s, %(likes)s, %(dislikes)s);"
        )
        new_id = connectToMySQL('railway').query_db(query, data)
        return new_id

    @classmethod
    def update_comment(cls, comment_id, data):
        query = (
            "UPDATE comments SET text=%(text)s, edited=%(edited)s WHERE id=%(id)s;"
        )
        data['id'] = comment_id
        return connectToMySQL('railway').query_db(query, data)

    @classmethod
    def delete_comment(cls, comment_id):
        query = "DELETE FROM comments WHERE id=%(comment_id)s;"
        data = {'comment_id': comment_id}
        return connectToMySQL('railway').query_db(query, data)

    @classmethod
    def like_comment(cls, comment_id, increment=True):
        operator = '+' if increment else '-'
        query = f"UPDATE comments SET likes = likes {operator} 1 WHERE id=%(comment_id)s;"
        data = {'comment_id': comment_id}
        return connectToMySQL('railway').query_db(query, data)

    @classmethod
    def dislike_comment(cls, comment_id, increment=True):
        operator = '+' if increment else '-'
        query = f"UPDATE comments SET dislikes = dislikes {operator} 1 WHERE id=%(comment_id)s;"
        data = {'comment_id': comment_id}
        return connectToMySQL('railway').query_db(query, data)
