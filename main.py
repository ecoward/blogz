from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy


db_name = 'blogz'
db_user = 'blogz'
db_pass = 'password'
db_server = 'localhost'
db_port = '8889'

app = Flask(__name__)
app.config['DEBUG'] = True      
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://'+db_user+':'+db_pass+'@'+db_server+':'+db_port+'/'+db_name
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'pclm62at&zp3C'

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(120))
    body = db.Column(db.Text(360))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique = True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password

db.create_all()

@app.route('/', methods=['GET'])
def index():
    users = User.query.all()
    return render_template('index.html', page_title= 'Blogz', users=users)


@app.before_request
def require_login():
    allowed_routes = ['index', 'login', 'signup', 'blog']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login') 


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            flash("Logged in")
            return redirect('/blog/newpost')
        else:
            flash('User password incorrect, or user does not exist', 'error')
    return render_template('login.html')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    username = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already in use', 'error')
        elif len(username) < 3 or len(password) < 3:
            flash('Invalid username or invalid password')
        elif password != verify:
            flash('Passwords do not match', 'error')
        elif not existing_user and password == verify:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/blog/newpost')
        
    return render_template('signup.html', username = username)


@app.route('/blog/newpost', methods=['POST', 'GET'])
def newpost():
    title = ""
    title_error = ""
    body = ""
    body_error = ""
    owner = User.query.filter_by(username = session['username']).first()

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']

        if not len(title) > 0:
            title_error = "Title must contain a value"
            
        if not len(body) > 0:
            body_error = "Body must contian a value"
         
        if not(title_error) and not(body_error):
            new_post = Blog(title = title, body = body, owner = owner )
            db.session.add(new_post)
            db.session.commit()
            db.session.refresh(new_post)
            return redirect('/blog?id='+ str(new_post.id))            
    
    return render_template('newpost.html', page_title="Add A Post", title=title, 
        title_error=title_error, body=body, body_error=body_error) 


@app.route('/blog', methods=['GET'])
def blog():
    blogs = []
    view = 'default'
    if request.args:
        id = request.args.get('id')
        username = request.args.get('user')
        if id:
            blogs.append(Blog.query.get(id))
            view = 'single'
        elif username:
            owner = User.query.filter_by(username = username).first()
            blogs = Blog.query.filter_by(owner = owner).all()
    else:
        blogs = Blog.query.all()
    return render_template('blog.html', page_title='Blogz', blogs=blogs,view=view)


@app.route('/logout')
def logout():
    del session['username']
    flash('Logged out')
    return redirect('/blog')


if __name__ == '__main__':
    app.run()