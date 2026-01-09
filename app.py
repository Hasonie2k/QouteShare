from flask import Flask, render_template, redirect, request, url_for, flash, session, abort
from flask_bcrypt import Bcrypt
from model import User
from model_q import Qoute
from model_c import Comment
import re
import datetime

app = Flask(__name__)
app.secret_key = 'very_secret'
bcrypt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

# ------------------- ROUTES -------------------

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
        q.author_name = author.user_name if author and author.user_name else (author.first_name if author else 'Unknown')
        q.comments = Comment.get_by_quote_id(q.id)

    last_quote = session.pop('last_quote', None)
    return render_template('home.html', user=user, quotes=quotes, last_quote=last_quote)

@app.route('/view/<name>')
def view(name):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    quote = Qoute.get_by_name(name)
    quotes = Qoute.get_all()
    return render_template('home.html', user=user, quotes=quotes, last_quote=quote)

@app.route('/create/quote')
def create():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    return render_template('create.html', user=user)

@app.route('/quote/save', methods=['POST'])
def add_quote():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not Qoute.validate_quote(request.form):
        flash('Invalid quote.')
        return redirect(url_for('home'))

    data = {
            'name': user.user_name or user.first_name,
            'comment': '',
            'qoute': request.form.get('qoute'),
            'users_id': user.id,
            'post_date': datetime.date.today().isoformat(),
            'likes': 0,
            'dislikes': 0
        }
    new_id = Qoute.save_quote(data)
    data['id'] = new_id
    session['last_quote'] = data
    return redirect(url_for('home'))

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
        'password': pw_hash
    }
    new_user_id = User.save_user(data)
    if not new_user_id:
        flash('Registration failed. Try again.')
        return redirect('/')
    session['user_id'] = new_user_id
    return redirect(url_for('home'))

# ------------------- COMMENTS -------------------

@app.route('/comment/<int:quote_id>', methods=['POST'])
def add_comment(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    text = request.form.get('comment_text', '').strip()
    if not text:
        flash('Comment cannot be empty.')
        return redirect(url_for('home'))
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

# ------------------- EDIT COMMENT -------------------
@app.route('/edit_comment/<int:quote_id>/<int:comment_idx>', methods=['GET', 'POST'])
def edit_comment(quote_id, comment_idx):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
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

# ------------------- EDIT/DELETE QUOTES -------------------

@app.route('/edit/quote/<int:quote_id>', methods=['GET', 'POST'])
def update_quote(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))
    
    quote = Qoute.get_by_id(quote_id)
    if not quote or quote.users_id != user.id:
        return redirect(url_for('home'))

    if request.method == 'POST':
        if not Qoute.validate_quote(request.form):
            return redirect(url_for('update_quote', quote_id=quote_id))
        import datetime
        data = {
            'id': quote.id,
            'name': user.user_name or user.first_name,
            'qoute': request.form.get('qoute'),
            'users_id': user.id,
            'post_date': datetime.date.today().isoformat(),
            'likes': quote.likes or 0,
            'dislikes': quote.dislikes or 0,
            'edited': True
        }
        Qoute.update_quote_by_id(data)
        return redirect(url_for('home'))

    return render_template('update.html', user=user, quote=quote)



@app.route('/delete_quote/<int:quote_id>', methods=['POST'])
def delete_quote_by_id(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
    quote = Qoute.get_by_id(quote_id)
    if quote and quote.users_id == user.id:
        Qoute.delete_quote_by_id(quote_id)
        flash('Quote deleted.')
    else:
        flash('You can only delete your own quotes.')
    return redirect(url_for('home'))

# ------------------- LIKE/DISLIKE QUOTES -------------------

@app.route('/like/<int:quote_id>', methods=['POST'])
def like_quote(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    quote = Qoute.get_by_id(quote_id)
    liked_quotes = set(session.get('liked_quotes', []))
    if str(quote_id) in liked_quotes:
        quote.likes = max((quote.likes or 1) - 1, 0)
        liked_quotes.remove(str(quote_id))
    else:
        quote.likes = (quote.likes or 0) + 1
        liked_quotes.add(str(quote_id))
    # Use only expected fields
    data = {
        'id': quote.id,
        'name': quote.name,
        'comment': quote.comment if hasattr(quote, 'comment') else '',
        'qoute': quote.qoute,
        'users_id': quote.users_id,
        'post_date': quote.post_date,
        'likes': quote.likes,
        'dislikes': quote.dislikes,
        'edited': getattr(quote, 'edited', False)
    }
    Qoute.update_quote_by_id(data)
    session['liked_quotes'] = list(liked_quotes)
    flash(f"Quote {quote_id} liked! New like count: {quote.likes}")
    return redirect(url_for('home'))

@app.route('/dislike/<int:quote_id>', methods=['POST'])
def dislike_quote(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    quote = Qoute.get_by_id(quote_id)
    disliked_quotes = set(session.get('disliked_quotes', []))
    if str(quote_id) in disliked_quotes:
        quote.dislikes = max((quote.dislikes or 1) - 1, 0)
        disliked_quotes.remove(str(quote_id))
    else:
        quote.dislikes = (quote.dislikes or 0) + 1
        disliked_quotes.add(str(quote_id))
    # Use only expected fields
    data = {
        'id': quote.id,
        'name': quote.name,
        'comment': quote.comment if hasattr(quote, 'comment') else '',
        'qoute': quote.qoute,
        'users_id': quote.users_id,
        'post_date': quote.post_date,
        'likes': quote.likes,
        'dislikes': quote.dislikes,
        'edited': getattr(quote, 'edited', False)
    }
    Qoute.update_quote_by_id(data)
    session['disliked_quotes'] = list(disliked_quotes)
    flash(f"Quote {quote_id} disliked! New dislike count: {quote.dislikes}")
    return redirect(url_for('home'))

# ------------------- LIKE/DISLIKE COMMENTS -------------------

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
    key = f'{quote_id}:{comment_idx}'
    if key in liked_comments:
        Comment.like_comment(comment.id, increment=False)
        liked_comments.remove(key)
    else:
        Comment.like_comment(comment.id, increment=True)
        liked_comments.add(key)
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
    key = f'{quote_id}:{comment_idx}'
    if key in disliked_comments:
        Comment.dislike_comment(comment.id, increment=False)
        disliked_comments.remove(key)
    else:
        Comment.dislike_comment(comment.id, increment=True)
        disliked_comments.add(key)
    session['disliked_comments'] = list(disliked_comments)
    return redirect(url_for('home'))

# ------------------- DELETE COMMENTS -------------------

@app.route('/delete_comment/<int:quote_id>/<int:comment_idx>', methods=['POST'])
def delete_comment(quote_id, comment_idx):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.get_by_id(session['user_id'])
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

# ------------------- RUN -------------------

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
