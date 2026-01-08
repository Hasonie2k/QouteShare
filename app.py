
from flask import Flask, render_template, redirect, request, url_for, flash, session
from model import User
from model_q import Qoute
import re
from flask_bcrypt import Bcrypt

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
    # attach author_name and comments from session
    comments = session.get('comments', {})
    for q in quotes:
        author = User.get_by_id(q.users_id)
        q.author_name = (author.user_name if author and getattr(author, 'user_name', None) else (author.first_name if author else 'Unknown'))
        q.comments = comments.get(str(q.id), [])

    last_quote = session.pop('last_quote', None)
    if last_quote:
        if isinstance(last_quote, dict):
            last_q = Qoute(last_quote)
        else:
            last_q = last_quote
        author = User.get_by_id(last_q.users_id)
        last_q.author_name = (author.user_name if author and getattr(author, 'user_name', None) else (author.first_name if author else 'Unknown'))
        last_q.comments = comments.get(str(getattr(last_q, 'id', '')), [])
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
    comments = session.get('comments', {})
    key = str(quote_id)
    comments.setdefault(key, []).append({
        'author': user.user_name or user.first_name,
        'text': text,
        'date': datetime.date.today().isoformat(),
        'edited': False
    })
    session['comments'] = comments
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
    comments = session.get('comments', {})
    key = str(quote_id)
    if key not in comments or not (0 <= comment_idx < len(comments[key])):
        flash('Comment not found.')
        return redirect(url_for('home'))
    comment = comments[key][comment_idx]
    if comment['author'] != (user.user_name or user.first_name):
        flash('You can only edit your own comments.')
        return redirect(url_for('home'))
    if request.method == 'POST':
        new_text = request.form.get('comment_text', '').strip()
        if not new_text:
            flash('Comment cannot be empty.')
            return redirect(url_for('home'))
        comment['text'] = new_text
        comment['edited'] = True
        session['comments'] = comments
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
    comments = session.get('comments', {})
    key = str(quote_id)
    if key in comments and 0 <= comment_idx < len(comments[key]):
        comment = comments[key][comment_idx]
        if comment['author'] == (user.user_name or user.first_name):
            comments[key].pop(comment_idx)
            session['comments'] = comments
            flash('Comment deleted.')
        else:
            flash('You can only delete your own comments.')
    else:
        flash('Comment not found.')
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)