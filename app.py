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

# ------------------- LIKE/DISLIKE QUOTES -------------------

@app.route('/like/<int:quote_id>', methods=['POST'])
def like_quote(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    quote = Qoute.get_by_id(quote_id)
    if not quote:
        abort(404)
    liked_quotes = set(session.get('liked_quotes', []))
    if str(quote_id) in liked_quotes:
        quote.likes = max((quote.likes or 1) - 1, 0)
        liked_quotes.remove(str(quote_id))
    else:
        quote.likes = (quote.likes or 0) + 1
        liked_quotes.add(str(quote_id))
    Qoute.update_quote_by_id(vars(quote))
    session['liked_quotes'] = list(liked_quotes)
    return redirect(url_for('home'))

@app.route('/dislike/<int:quote_id>', methods=['POST'])
def dislike_quote(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    quote = Qoute.get_by_id(quote_id)
    if not quote:
        abort(404)
    disliked_quotes = set(session.get('disliked_quotes', []))
    if str(quote_id) in disliked_quotes:
        quote.dislikes = max((quote.dislikes or 1) - 1, 0)
        disliked_quotes.remove(str(quote_id))
    else:
        quote.dislikes = (quote.dislikes or 0) + 1
        disliked_quotes.add(str(quote_id))
    Qoute.update_quote_by_id(vars(quote))
    session['disliked_quotes'] = list(disliked_quotes)
    return redirect(url_for('home'))

# ------------------- RUN -------------------

if __name__ == "__main__":
    # For deployment, Railway automatically sets PORT
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
