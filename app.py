import os
from flask import Flask, render_template, redirect, request, url_for, flash, session, abort
from flask_bcrypt import Bcrypt
import re
import datetime
from model import User
from model_q import Qoute
from model_c import Comment

app = Flask(__name__)
app.secret_key = 'very_secret'
bcrypt = Bcrypt(app)
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

# ------------------ LOGIN / REGISTER ------------------

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


@app.route('/register/user', methods=['POST'])
def add_user():
    # you can remove validation if you want
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
    return redirect(url_for('home'))

# ------------------ HOME / QUOTES ------------------

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
        q.author_name = author.user_name if author and getattr(author, 'user_name', None) else (author.first_name if author else 'Unknown')
        q.comments = Comment.get_by_quote_id(q.id)

    last_quote = session.pop('last_quote', None)
    if last_quote:
        if isinstance(last_quote, dict):
            last_q = Qoute(last_quote)
        else:
            last_q = last_quote
        author = User.get_by_id(last_q.users_id)
        last_q.author_name = author.user_name if author and getattr(author, 'user_name', None) else (author.first_name if author else 'Unknown')
        last_q.comments = Comment.get_by_quote_id(getattr(last_q, 'id', ''))
        last_quote = last_q

    return render_template('home.html', user=user, quotes=quotes, last_quote=last_quote)

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

# ------------------ QUOTE CRUD ------------------

@app.route('/quote/save', methods=['POST'])
def add_quote():
    if 'user_id' not in session:
        flash('You must log in to post a quote.')
        return redirect(url_for('login'))

    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.')
        return redirect(url_for('login'))

    quote_text = request.form.get('qoute', '').strip()
    if not Qoute.validate_quote({'qoute': quote_text}):
        return redirect(url_for('home'))

    data = {
        'name': user.user_name if user.user_name else user.first_name,
        'comment': '',
        'qoute': quote_text,
        'users_id': user.id,
        'post_date': datetime.date.today().isoformat(),
        'dislikes': 0,
        'likes': 0,
    }

    new_id = Qoute.save_quote(data)
    if new_id:
        data['id'] = new_id
        session['last_quote'] = data
        flash('Quote added successfully!')
    else:
        flash('Failed to add quote. Please try again.')

    return redirect(url_for('home'))


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
        flash('Quote deleted.')
    else:
        flash('You can only delete your own quotes.')
    return redirect(url_for('home'))

# ------------------ LIKE / DISLIKE QUOTE ------------------

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
        # unlike
        new_likes = max((quote.likes or 1) - 1, 0)
        liked_quotes.remove(str(quote_id))
        flash('You unliked this quote!')
    else:
        new_likes = (quote.likes or 0) + 1
        liked_quotes.add(str(quote_id))
        flash('You liked this quote!')

    Qoute.update_quote_by_id({
        'id': quote.id,
        'name': quote.name,
        'comment': quote.comment,
        'qoute': quote.qoute,
        'users_id': quote.users_id,
        'post_date': quote.post_date,
        'likes': new_likes,
        'dislikes': quote.dislikes or 0
    })
    session['liked_quotes'] = list(liked_quotes)
    return redirect(url_for('home'))

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
        new_dislikes = max((quote.dislikes or 1) - 1, 0)
        disliked_quotes.remove(str(quote_id))
        flash('Removed dislike!')
    else:
        new_dislikes = (quote.dislikes or 0) + 1
        disliked_quotes.add(str(quote_id))
        flash('You disliked this quote!')

    Qoute.update_quote_by_id({
        'id': quote.id,
        'name': quote.name,
        'comment': quote.comment,
        'qoute': quote.qoute,
        'users_id': quote.users_id,
        'post_date': quote.post_date,
        'likes': quote.likes or 0,
        'dislikes': new_dislikes
    })
    session['disliked_quotes'] = list(disliked_quotes)
    return redirect(url_for('home'))

# ------------------ COMMENTS ------------------

@app.route('/comment/<int:quote_id>', methods=['POST'])
def add_comment(quote_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.get_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired.')
        return redirect(url_for('login'))

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
    flash('Comment added!')
    return redirect(url_for('home'))

# ------------------ RUN APP ------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
