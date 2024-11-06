from flask import Flask, request, jsonify, render_template, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired, EqualTo
import random
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

# Create the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smart_bin.db'
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    user_password = db.Column(db.String(100), nullable=False)
    session_count = db.Column(db.Integer, default=0)
    userlv = db.Column(db.Integer, default=0)
    sessions = db.relationship('Session', backref='user', lazy='dynamic')
    leaderboard_entry = db.relationship('Leaderboard', backref='user', uselist=False)

    def generate_user_id(self):
        while True:
            id = str(random.randint(10000000, 99999999))
            existing_user = User.query.filter_by(id=id).first()
            if not existing_user:
                self.id = id
                return self.id

class Session(db.Model):
    sessionid = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_of_usage = db.Column(db.DateTime, nullable=False)
    time_used = db.Column(db.Interval, nullable=False)
    bin_id = db.Column(db.Integer, db.ForeignKey('bin.bin_id'), nullable=False)
    trash_count = db.Column(db.Integer, default=0)

class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    user_score = db.Column(db.Integer, default=0)

class Bin(db.Model):
    bin_id = db.Column(db.Integer, primary_key=True)
    bin_full = db.Column(db.Boolean, default=False)
    bin_type = db.Column(db.String(50), nullable=False)
    bin_location = db.Column(db.String(100), nullable=False)
    sessions = db.relationship('Session', backref='bin', lazy='dynamic')

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=50)], render_kw={"placeholder": "Username"})
    user_password = PasswordField(validators=[InputRequired(), Length(min=8, max=50)], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField('confirm_password', validators=[DataRequired(), EqualTo('user_password')], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=50)], render_kw={"placeholder": "Username"})
    user_password = PasswordField(validators=[InputRequired(), Length(min=8, max=50)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.user_password.data)
        new_user = User(username=form.username.data, user_password=hashed_password)
        new_user.generate_user_id()
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('manage_users'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.user_password, form.user_password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('manage_users'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/manage_users')
@login_required
def manage_users():
    users = User.query.all()
    return render_template('manage_users.html', users=users, current_user=current_user)



if __name__ == '__main__':
    app.run(debug=True)