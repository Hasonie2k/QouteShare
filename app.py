
from flask import Flask, render_template, redirect, request, url_for, flash, session
from model import User
from model_q import Qoute
from model_c import Comment
import re
from flask_bcrypt import Bcrypt

from flask import abort

app = Flask(__name__)
app.secret_key = 'very_secret'
bcrypt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')


@app.route('/')
def log_reg():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.get_by_email(email)
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        flash('Invalid email or password.')
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('log_reg'))


@app.route('/menu')
def menu():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))
    quotes = Qoute.get_all()
    return render_template('home.html', user=user, quotes=quotes, users_id=user.id)


@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))
    quotes = Qoute.get_all()
    for q in quotes:
        author = User.get_by_id(q.users_id)
        q.author_name = (author.user_name if author and getattr(author, 'user_name', None) else (author.first_name if author else 'Unknown'))
        q.comments = Comment.get_by_quote_id(q.id)

    last_quote = session.pop('last_quote', None)
    if last_quote:
        if isinstance(last_quote, dict):
            last_q = Qoute(last_quote)
        else:
            last_q = last_quote
        author = User.get_by_id(last_q.users_id)
        last_q.author_name = (author.user_name if author and getattr(author, 'user_name', None) else (author.first_name if author else 'Unknown'))
        last_q.comments = Comment.get_by_quote_id(getattr(last_q, 'id', ''))
        last_quote = last_q

    return render_template('home.html', user=user, quotes=quotes, last_quote=last_quote)


@app.route('/view/<name>', methods=['GET'])
def view(name):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))
    quote = Qoute.get_by_name(name)
    quotes = Qoute.get_all()
    return render_template('home.html', user=user, quotes=quotes, last_quote=quote)


@app.route('/create/quote')
def create():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))
    return render_template('create.html', user=user)



@app.route('/comment/<int:quote_id>', methods=['POST'])
def add_comment(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))
    text = request.form.get('comment_text', '').strip()
    if not text:
        flash('Comment cannot be empty.')
        return redirect(url_for('home'))
    import datetime
    data = {
        'quote_id': quote_id,
        'user_id': user.id,
        'author': user.user_name or user.first_name,
        'text': text,
        'date': datetime.date.today().isoformat(),
        'edited': False,
        'likes': 0,
        'dislikes': 0
    }
    Comment.add_comment(data)
    return redirect(url_for('home'))

# Add route to update a comment
@app.route('/edit_comment/<int:quote_id>/<int:comment_idx>', methods=['GET', 'POST'])
def edit_comment(quote_id, comment_idx):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))
    comments = Comment.get_by_quote_id(quote_id)
    if not (0 <= comment_idx < len(comments)):
        flash('Comment not found.')
        return redirect(url_for('home'))
    comment = comments[comment_idx]
    if comment.author != (user.user_name or user.first_name):
        flash('You can only edit your own comments.')
        return redirect(url_for('home'))
    if request.method == 'POST':
        new_text = request.form.get('comment_text', '').strip()
        if not new_text:
            flash('Comment cannot be empty.')
            return redirect(url_for('home'))
        Comment.update_comment(comment.id, {'text': new_text, 'edited': True})
        return redirect(url_for('home'))
    return render_template('edit_comment.html', user=user, comment=comment, quote_id=quote_id, comment_idx=comment_idx)


@app.route('/update/quote', methods=['POST', 'GET'])
def update():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))
    quote = Qoute.get_by_id(session['user_id'])
    return render_template('update.html', user=user, quote=quote)


@app.route('/delete_quote/<int:users_id>', methods=['POST'])
def delete_quote(users_id):
    quote = Qoute.get_by_id(users_id)
    if quote is not None and quote.users_id == session.get('user_id'):
        Qoute.delete_quote_by_id(users_id)
    return redirect(url_for('menu'))


@app.route('/register/user', methods=['POST'])
def add_user():
    if not User.validate_user(request.form):
        return redirect('/')
    pw_hash = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
    data = {
        'first_name': request.form['first_name'],
        'last_name': request.form['last_name'],
        'user_name': request.form.get('user_name', ''),
        'email': request.form['email'],
        'password': pw_hash,
    }
    new_user_id = User.save_user(data)
    if not new_user_id:
        flash('Registration failed; please try again.')
        return redirect('/')
    session['user_id'] = new_user_id
    return redirect(url_for('menu'))


@app.route('/quote/save', methods=['POST'])
def add_quote():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))
    if not Qoute.validate_quote(request.form):
        flash('Invalid quote submission.')
        return redirect(url_for('home'))
    import datetime
    data = {
        'name': user.user_name if user.user_name else user.first_name,
        'comment': '',
        'qoute': request.form.get('qoute'),
        'users_id': session['user_id'],
        'post_date': datetime.date.today().isoformat(),
        'dislikes': 0,
        'likes': 0,
    }
    new_id = Qoute.save_quote(data)
    data['id'] = new_id
    # store last submitted data in session and redirect to avoid duplicate posts on refresh
    session['last_quote'] = data
    return redirect(url_for('home'))


@app.route('/edit/quote/<int:users_id>', methods=['GET', 'POST'])
def update_quote(users_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))
    quote = Qoute.get_by_id(users_id)
    if quote is None or quote.users_id != user.id:
        return redirect(url_for('menu'))
    if request.method == 'POST':
        if not Qoute.validate_quote(request.form):
            return redirect(url_for('update_quote', users_id=users_id))
        import datetime
        data = {
            'id': quote.id,
            'name': user.user_name if user.user_name else user.first_name,
            'comment': request.form.get('comment'),
            'qoute': request.form.get('qoute'),
            'users_id': user.id,
            'post_date': datetime.date.today().isoformat(),
            'dislikes': quote.dislikes or 0,
            'likes': quote.likes or 0,
            'edited': True
        }
        session.setdefault('edited_quotes', set())
        edited_quotes = set(session.get('edited_quotes', []))
        edited_quotes.add(quote.id)
        session['edited_quotes'] = list(edited_quotes)
        Qoute.update_quote_by_id(data)
        return redirect(url_for('home'))
    return render_template('update.html', user=user, quote=quote)

@app.route('/delete_quote/<int:quote_id>', methods=['POST'])
def delete_quote_by_id(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))
    quote = Qoute.get_by_id(quote_id)
    if quote and quote.users_id == user.id:
        Qoute.delete_quote_by_id(quote_id)
        comments = session.get('comments', {})
        comments.pop(str(quote_id), None)
        session['comments'] = comments
        flash('Quote deleted.')
    else:
        flash('You can only delete your own quotes.')
    return redirect(url_for('home'))

@app.route('/delete_comment/<int:quote_id>/<int:comment_idx>', methods=['POST'])
def delete_comment(quote_id, comment_idx):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))
    comments = Comment.get_by_quote_id(quote_id)
    if not (0 <= comment_idx < len(comments)):
        flash('Comment not found.')
        return redirect(url_for('home'))
    comment = comments[comment_idx]
    if comment.author == (user.user_name or user.first_name):
        Comment.delete_comment(comment.id)
        flash('Comment deleted.')
    else:
        flash('You can only delete your own comments.')
    return redirect(url_for('home'))



# Route to handle liking a quote
@app.route('/like/<int:quote_id>', methods=['POST'])
def like_quote(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    liked_quotes = set(session.get('liked_quotes', []))
    quote = Qoute.get_by_id(quote_id)
    if not quote:
        abort(404)
    if str(quote_id) in liked_quotes:
        # Unlike: decrement likes (not below 0)
        new_likes = max((quote.likes or 1) - 1, 0)
        liked_quotes.remove(str(quote_id))
        flash('You unliked this quote!')
    else:
        # Like: increment likes
        new_likes = (quote.likes or 0) + 1
        liked_quotes.add(str(quote_id))
        flash('You liked this quote!')
    data = {
        'id': quote.id,
        'name': quote.name,
        'comment': quote.comment,
        'qoute': quote.qoute,
        'users_id': quote.users_id,
        'post_date': quote.post_date,
        'dislikes': quote.dislikes or 0,
        'likes': new_likes
    }
    Qoute.update_quote_by_id(data)
    session['liked_quotes'] = list(liked_quotes)
    return redirect(url_for('home'))

# Route to handle disliking a quote (toggle)
@app.route('/dislike/<int:quote_id>', methods=['POST'])
def dislike_quote(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    disliked_quotes = set(session.get('disliked_quotes', []))
    quote = Qoute.get_by_id(quote_id)
    if not quote:
        abort(404)
    if str(quote_id) in disliked_quotes:
        # Remove dislike
        new_dislikes = max((quote.dislikes or 1) - 1, 0)
        disliked_quotes.remove(str(quote_id))
        flash('You removed your dislike!')
    else:
        # Add dislike
        new_dislikes = (quote.dislikes or 0) + 1
        disliked_quotes.add(str(quote_id))
        flash('You disliked this quote!')
    data = {
        'id': quote.id,
        'name': quote.name,
        'comment': quote.comment,
        'qoute': quote.qoute,
        'users_id': quote.users_id,
        'post_date': quote.post_date,
        'dislikes': new_dislikes,
        'likes': quote.likes or 0
    }
    Qoute.update_quote_by_id(data)
    session['disliked_quotes'] = list(disliked_quotes)
    return redirect(url_for('home'))

# Like/dislike a comment (toggle)
@app.route('/like_comment/<int:quote_id>/<int:comment_idx>', methods=['POST'])
def like_comment(quote_id, comment_idx):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    comments = Comment.get_by_quote_id(quote_id)
    if not (0 <= comment_idx < len(comments)):
        flash('Comment not found.')
        return redirect(url_for('home'))
    comment = comments[comment_idx]
    liked_comments = set(session.get('liked_comments', []))
    comment_key = f'{quote_id}:{comment_idx}'
    if comment_key in liked_comments:
        # Unlike
        Comment.like_comment(comment.id, increment=False)
        liked_comments.remove(comment_key)
    else:
        # Like
        Comment.like_comment(comment.id, increment=True)
        liked_comments.add(comment_key)
    session['liked_comments'] = list(liked_comments)
    return redirect(url_for('home'))

@app.route('/dislike_comment/<int:quote_id>/<int:comment_idx>', methods=['POST'])
def dislike_comment(quote_id, comment_idx):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    comments = Comment.get_by_quote_id(quote_id)
    if not (0 <= comment_idx < len(comments)):
        flash('Comment not found.')
        return redirect(url_for('home'))
    comment = comments[comment_idx]
    disliked_comments = set(session.get('disliked_comments', []))
    comment_key = f'{quote_id}:{comment_idx}'
    if comment_key in disliked_comments:
        # Remove dislike
        Comment.dislike_comment(comment.id, increment=False)
        disliked_comments.remove(comment_key)
    else:
        # Add dislike
        Comment.dislike_comment(comment.id, increment=True)
        disliked_comments.add(comment_key)
    session['disliked_comments'] = list(disliked_comments)
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
