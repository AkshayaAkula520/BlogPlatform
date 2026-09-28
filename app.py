from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')

# MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = 'blog_platform'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


@app.route('/')
def home():
    if 'user_id' in session:
        return f"Welcome, {session['username']}! You are logged in."

    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        cursor = mysql.connection.cursor()

        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_password)
        )

        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']

            return redirect(url_for('home'))

        return "Invalid email or password"

    return render_template('login.html')

@app.route('/posts')
def posts():
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT posts.*, users.username
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
    """)

    all_posts = cursor.fetchall()

    for post in all_posts:
        cursor.execute("""
            SELECT comments.*, users.username
            FROM comments
            JOIN users ON comments.user_id = users.id
            WHERE comments.post_id = %s
            ORDER BY comments.created_at ASC
        """, (post['id'],))

        post['comments'] = cursor.fetchall()

    cursor.close()

    return render_template('index.html', posts=all_posts)
@app.route('/create-post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        cursor = mysql.connection.cursor()

        cursor.execute(
            "INSERT INTO posts (user_id, title, content) VALUES (%s, %s, %s)",
            (session['user_id'], title, content)
        )

        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('posts'))

    return render_template('create_post.html')

@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()

    cursor.execute(
        "SELECT * FROM posts WHERE id = %s AND user_id = %s",
        (post_id, session['user_id'])
    )

    post = cursor.fetchone()

    if not post:
        cursor.close()
        return "Post not found or you are not allowed to edit it."

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        cursor.execute(
            """
            UPDATE posts
            SET title = %s, content = %s
            WHERE id = %s AND user_id = %s
            """,
            (title, content, post_id, session['user_id'])
        )

        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('posts'))

    cursor.close()

    return render_template('edit_post.html', post=post)

@app.route('/delete-post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()

    cursor.execute(
        "DELETE FROM posts WHERE id = %s AND user_id = %s",
        (post_id, session['user_id'])
    )

    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('posts'))
@app.route('/comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    comment = request.form['comment']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        INSERT INTO comments (post_id, user_id, comment)
        VALUES (%s, %s, %s)
        """,
        (post_id, session['user_id'], comment)
    )

    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('posts'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)