from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta, date, time
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired, EqualTo
import random
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import plotly.offline as pyo
from heatmap import heatmap, streak
import pytz
import logging
from functools import wraps

temp_sessions = {}


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

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.userlv != 1:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function


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
            id = random.randint(10000000, 99999999)
            existing_user = User.query.filter_by(id=id).first()
            if not existing_user:
                self.id = id
                return self.id

class Session(db.Model):
    sessionid = db.Column(db.Integer, primary_key=True)#identifier of each session
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)#who is in the session
    session_date = db.Column(db.Date, nullable=False)#date of use
    session_time = db.Column(db.Time, nullable=False)#time of use
    time_used = db.Column(db.Interval, nullable=False)#how long the user used 
    bin_id = db.Column(db.Integer, db.ForeignKey('bin.bin_id'), nullable=False)#which bin
    trash_count = db.Column(db.Integer, default=0)#how much rubbish

class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    
    user_score = db.Column(db.Integer, default=1)
    

class Bin(db.Model):
    bin_id = db.Column(db.Integer, primary_key=True)
    bin_full = db.Column(db.Boolean, default=False)
    bin_type = db.Column(db.String(50), nullable=False)
    bin_location = db.Column(db.String(100), nullable=False)
    sessions = db.relationship('Session', backref='bin', lazy='dynamic')

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=50)], render_kw={"placeholder": "Username"})
    user_password = PasswordField(validators=[InputRequired(), Length(min=8, max=50)], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('user_password')], render_kw={"placeholder": "Confirm Password"})
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


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)



# Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        log_message()
    return render_template('home.html')

def log_message():
    logging.info('scan qrcode')

@app.route('/static/qrbutton.js')
def qrbutton_js():
    return app.send_static_file('qrbutton.js')


@app.route('/about')
def about():
    if request.method == 'POST':
        log_message()
    return render_template('about.html')

@app.route('/while_throwing')
def while_throwing():
    return render_template('while_throwing.html')

@app.route('/after_throwing')
def after_throwing():
    if request.method == 'POST':
        log_message()
    return render_template('after_throwing.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        log_message()
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
    if request.method == 'POST':
        log_message()
    if current_user.is_authenticated:
        return redirect(url_for('personal_page'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.user_password, form.user_password.data):
            login_user(user)
            flash('Logged out successfully!', 'success')
            return redirect(url_for('personal_page'))
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
    if request.method == 'POST':
        log_message()
    users = User.query.all()
    return render_template('manage_users.html', users=users, current_user=current_user)



@app.route('/update_user_role/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role == 'user':
        user.userlv = 0
        db.session.commit()
    elif new_role == 'admin':
        user.userlv = 1
        db.session.commit()
    return redirect(url_for('manage_users'))

@app.route('/manage_bins')
@login_required
@admin_required
def manage_bins():
    if request.method == 'POST':
        log_message()
    bins = Bin.query.all()
    return render_template('manage_bins.html', bins=bins)

@app.route('/qrcode', methods=['POST'])
@login_required 
def qrcode():
    try:
        # Get bin_id directly from request data
        bin_id = request.get_data(as_text=True)
        
         #Validate bin_id is a valid integer
        try:
            bin_id = int(bin_id)
        except ValueError:
            return jsonify({'error': 'Invalid bin_id format. Must be an integer'}), 400
            
        user_id = current_user.id 
        
        # Verify bin exists
        bin_exists = Bin.query.get(bin_id)
        if not bin_exists:
            return jsonify({'error': 'Bin not found'}), 404
        
        # Store start time temporarily
        current_time = datetime.now(pytz.UTC)
        temp_sessions[f"{user_id}_{bin_id}"] = current_time
        
        return redirect(url_for('while_throwing'))
            
 
        
    except Exception as e:
        logging.error(f"Error in qrcode endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/end_session', methods=['POST'])
def end_session():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        bin_id = data.get('bin_id')
        trash_count = data.get('trash_count', 0)
        
        if not user_id or not bin_id:
            return jsonify({'error': 'Missing user_id or bin_id'}), 400
        
        session_key = f"{user_id}_{bin_id}"
        start_time = temp_sessions.get(session_key)
        
        if not start_time:
            return jsonify({'error': 'No active session found'}), 404
        
        # Calculate session duration
        end_time = datetime.now(pytz.UTC)
        duration = end_time - start_time
        
        # Create new session record
        new_session = Session(
            user_id=user_id,
            bin_id=bin_id,
            session_date=date.today(),
            session_time=start_time.time(),
            time_used=duration,
            trash_count=trash_count
        )
        
        # Update user's session count
        user = User.query.get(user_id)
        if user:
            user.session_count += 1
            
            # Update or create leaderboard entry
            leaderboard = Leaderboard.query.filter_by(user_id=user_id).first()
            if not leaderboard:
                leaderboard = Leaderboard(
                    user_id=user_id,
                    user_score=trash_count  # Initialize with current trash count
                )
                db.session.add(leaderboard)
            else:
                # Ensure user_score is initialized if it's None
                if leaderboard.user_score is None:
                    leaderboard.user_score = 0
                leaderboard.user_score += trash_count
        
            try:
                db.session.add(new_session)
                db.session.commit()
                # Clean up temporary session data
                del temp_sessions[session_key]
                
                return redirect(url_for('after_throwing'))
                
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 500
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_bin', methods=['POST'])
def add_bin():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        required_fields = ['bin_id', 'bin_type', 'bin_location']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        bin_id = data['bin_id']
        bin_type = data['bin_type']
        bin_location = data['bin_location']
        bin_full = data.get('bin_full', False)  # Default to False if not provided

        # Check if bin exists
        existing_bin = Bin.query.get(bin_id)

        if existing_bin:
            # Update existing bin
            existing_bin.bin_full = bin_full
            existing_bin.bin_type = bin_type
            existing_bin.bin_location = bin_location
            
            db.session.commit()
            
            return jsonify({
                "message": "Bin updated successfully",
                "bin": {
                    "bin_id": existing_bin.bin_id,
                    "bin_type": existing_bin.bin_type,
                    "bin_location": existing_bin.bin_location,
                    "bin_full": existing_bin.bin_full
                }
            }), 200
        else:
            # Create new bin
            new_bin = Bin(
                bin_id=bin_id,
                bin_full=bin_full,
                bin_type=bin_type,
                bin_location=bin_location
            )
            
            db.session.add(new_bin)
            db.session.commit()
            
            return jsonify({
                "message": "New bin added successfully",
                "bin": {
                    "bin_id": new_bin.bin_id,
                    "bin_type": new_bin.bin_type,
                    "bin_location": new_bin.bin_location,
                    "bin_full": new_bin.bin_full
                }
            }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to process request",
            "details": str(e)
        }), 500



@app.route('/personal_page')
@login_required
def personal_page():
    if request.method == 'POST':
        log_message()
    # Get all sessions for the current user
    user_sessions = Session.query.filter_by(user_id=current_user.id).all()
    
    # Format the dates for the heatmap
    data = []
    for session in user_sessions:
        date_str = session.session_date.strftime('%Y-%m-%d')
        data.append(date_str)

    plot_html = pyo.plot(
        figure_or_data = heatmap(data=data, weeks=25, width=600,height=200),
        output_type = 'div',
        config = {
            "displaylogo": False,
            'modeBarButtonsToRemove': ['pan2d','lasso2d','toImage'],
        },
    )

    date_format = "%Y-%m-%d"

    recycling_last_month, recycling_last_month_start, recycling_last_month_end, \
    longest_streak, longest_streak_start, longest_streak_end, \
    current_streak, current_streak_start, current_streak_end, current_streak_ago = streak(data)

    # Get user's statistics from database
    total_sessions = current_user.session_count
    total_trash = db.session.query(db.func.sum(Session.trash_count))\
        .filter_by(user_id=current_user.id).scalar() or 0
    
    # Get user's leaderboard position
    leaderboard_entry = Leaderboard.query.filter_by(user_id=current_user.id).first()
    user_score = leaderboard_entry.user_score if leaderboard_entry else 0

    recycling_last_month_dates = "" if recycling_last_month == 0 else f"From: {recycling_last_month_start.strftime(date_format)} To: {recycling_last_month_end.strftime(date_format)}"
    longest_streak_dates = "" if longest_streak == 0 else f"From: {longest_streak_start.strftime(date_format)} To: {longest_streak_end.strftime(date_format)}"
    current_streak_dates = (f"Last recycled {current_streak_ago} days ago" if current_streak_ago > 0 else "") if current_streak == 0 else f"From: {current_streak_start.strftime(date_format)} To: {current_streak_end.strftime(date_format)}"

    return render_template(
        'personal_page.html', 
        plot=plot_html,
        recycling_last_month=f"{recycling_last_month} total",
        longest_streak=f"{longest_streak} days",
        current_streak=f"{current_streak} days",
        recycling_last_month_dates=recycling_last_month_dates,
        longest_streak_dates=longest_streak_dates,
        current_streak_dates=current_streak_dates,
        total_sessions=total_sessions,
        total_trash=total_trash,
        user_score=user_score,
        username=current_user.username
    )




@app.route('/leaderboard')
@login_required
def leaderboard():
    if request.method == 'POST':
        log_message()
    # Calculate total trash count for each user
    user_totals = db.session.query(
        User.id,
        User.username,
        db.func.sum(Session.trash_count).label('total_trash')
    ).join(Session, User.id == Session.user_id)\
     .group_by(User.id)\
     .order_by(db.func.sum(Session.trash_count).desc())\
     .all()

    # Create ranked list with user data
    ranked_users = []
    for index, (user_id, username, total_trash) in enumerate(user_totals, 1):
        ranked_users.append({
            'rank': index,
            'username': username,
            'trash_count': int(total_trash or 0),
            'is_current': user_id == current_user.id
        })
    
    # Find current user's rank
    current_user_rank = next(
        (user for user in ranked_users if user['is_current']),
        {'rank': '-', 'username': current_user.username, 'trash_count': 0, 'is_current': True}
    )

    return render_template('leaderboard.html', 
                         leaderboard=ranked_users, 
                         current_user_rank=current_user_rank)


if __name__ == '__main__':
    app.run(debug=True)