from mysqlconnection import connectToMySQL

class Comment:
	def __init__(self, data):
		self.id = data.get('id')
		self.quote_id = data.get('quote_id')
		self.user_id = data.get('user_id')
		self.author = data.get('author')
		self.text = data.get('text')
		self.date = data.get('date')
		self.edited = data.get('edited', False)
		self.likes = data.get('likes', 0)
		self.dislikes = data.get('dislikes', 0)

	@classmethod
	def get_by_quote_id(cls, quote_id):
		query = "SELECT * FROM comments WHERE quote_id = %(quote_id)s ORDER BY id ASC;"
		data = {'quote_id': quote_id}
		results = connectToMySQL('qouteschema').query_db(query, data)
		return [cls(row) for row in results] if results else []

	@classmethod
	def get_by_id(cls, comment_id):
		query = "SELECT * FROM comments WHERE id = %(id)s;"
		data = {'id': comment_id}
		result = connectToMySQL('qouteschema').query_db(query, data)
		if result and len(result) > 0:
			return cls(result[0])
		return None

	@classmethod
	def add_comment(cls, data):
		query = ("INSERT INTO comments (quote_id, user_id, author, text, date, edited, likes, dislikes) "
				 "VALUES (%(quote_id)s, %(user_id)s, %(author)s, %(text)s, %(date)s, %(edited)s, %(likes)s, %(dislikes)s);")
		return connectToMySQL('qouteschema').query_db(query, data)

	@classmethod
	def update_comment(cls, comment_id, data):
		set_clause = ', '.join([f"{k}=%({k})s" for k in data.keys()])
		query = f"UPDATE comments SET {set_clause} WHERE id = %(id)s;"
		data['id'] = comment_id
		return connectToMySQL('qouteschema').query_db(query, data)

	@classmethod
	def delete_comment(cls, comment_id):
		query = "DELETE FROM comments WHERE id = %(id)s;"
		data = {'id': comment_id}
		return connectToMySQL('qouteschema').query_db(query, data)

	@classmethod
	def like_comment(cls, comment_id, increment=True):
		op = '+' if increment else '-'
		query = f"UPDATE comments SET likes = GREATEST(likes {op} 1, 0) WHERE id = %(id)s;"
		data = {'id': comment_id}
		return connectToMySQL('qouteschema').query_db(query, data)

	@classmethod
	def dislike_comment(cls, comment_id, increment=True):
		op = '+' if increment else '-'
		query = f"UPDATE comments SET dislikes = GREATEST(dislikes {op} 1, 0) WHERE id = %(id)s;"
		data = {'id': comment_id}
		return connectToMySQL('qouteschema').query_db(query, data)
