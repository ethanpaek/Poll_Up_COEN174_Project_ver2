import os
from flask import Flask, render_template, request, flash, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from models import db, Users, Votes, Polls, Options, UserPolls
from flask_admin import Admin
from admin import AdminView, TopicView

# Blueprints
from api.api import api

# celery factory
from celery import Celery


def make_celery(poll_up):
    celery = Celery(
        poll_up.import_name, backend=poll_up.config['CELERY_RESULT_BACKEND'],
        broker=poll_up.config['CELERY_BROKER']
    )
    celery.conf.update(poll_up.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with poll_up.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask

    return celery


poll_up = Flask(__name__)

poll_up.register_blueprint(api)

# load config from the config file we created earlier
if os.getenv('APP_MODE') == "PRODUCTION":
    poll_up.config.from_object('production_settings')
else:
    poll_up.config.from_object('config')

db.init_app(poll_up)  # Initialize the database
db.create_all(app=poll_up)  # Create the database

migrate = Migrate(poll_up, db, render_as_batch=True)

# create celery object
celery = make_celery(poll_up)

admin = Admin(poll_up, name='Dashboard', index_view=TopicView(Polls, db.session, url='/admin', endpoint='admin'))
admin.add_view(AdminView(Users, db.session))
admin.add_view(AdminView(Votes, db.session))
admin.add_view(AdminView(Options, db.session))
admin.add_view(AdminView(UserPolls, db.session))


@poll_up.route('/')
def home():
    return render_template('index.html')


@poll_up.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # get the user details from the form
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        # hash the password
        password = generate_password_hash(password)

        user = Users(email=email, username=username, password=password)

        db.session.add(user)
        db.session.commit()

        flash('Thanks for signing up! Please login')

        return redirect(url_for('home'))

    # it's a GET request, just render the template
    return render_template('signup.html')


@poll_up.route('/login', methods=['POST'])
def login():
    # we don't need to check the request type as flask will raise a bad request
    # error if a request aside from POST is made to this url

    username = request.form['username']
    password = request.form['password']

    # search the database for the User
    user = Users.query.filter_by(username=username).first()

    if user:
        password_hash = user.password

        if check_password_hash(password_hash, password):
            # The hash matches the password in the database log the user in
            session['user'] = username

            flash('Login was successful')
    else:
        # user wasn't found in the database
        flash('Username or password is incorrect please try again', 'error')

    return redirect(request.args.get('next') or url_for('home'))


@poll_up.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user')

        flash('We hope to see you again!')

    return redirect(url_for('home'))


@poll_up.route('/polls', methods=['GET'])
def polls():
    return render_template('polls.html')


@poll_up.route('/polls/<poll_name>')
def poll(poll_name):
    return render_template('index.html')


@poll_up.route('/about')
def about():
    return render_template('aboutme.html')

@poll_up.route('/aboutthepolls')
def aboutthepolls():
    return render_template('aboutthepolls.html')
