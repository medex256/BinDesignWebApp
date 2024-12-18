from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, date
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired, EqualTo
import random
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import plotly.offline as pyo
from heatmap import heatmap, streak
#from garbageclassification import garbage_classification
import pytz
import logging
from functools import wraps
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import requests
#☆*: .｡. o(≧▽≦)o .｡.:*☆
temp_sessions = {}

#(┬┬﹏┬┬)
# Create the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smart_bin.db'
app.config['SECRET_KEY'] = 'reswzxdfcgh87654rg9876tcf876tgu6cfghiuuytfjklmnbvcxzqwerts4vkuyr6esx'



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
        if not current_user.is_authenticated or current_user.userlv != 'Admin':
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function


# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    user_password = db.Column(db.String(100), nullable=False)
    session_count = db.Column(db.Integer, default=0)
    userlv = db.Column(db.String(80), nullable=False, default='User')
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
    end_time = db.Column(db.Time, nullable=True)
    time_used = db.Column(db.Interval, nullable=True)#how long the user used 
    bin_id = db.Column(db.Integer, db.ForeignKey('bin.bin_id'), nullable=False)#which bin
    trash_count = db.Column(db.Integer, default=0)#how much rubbish
    active = db.Column(db.Boolean, default=True)

    #user = db.relationship('User')
    #bin = db.relationship('Bin')

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
    active_session = Session.query.filter_by(user_id=current_user.id, active=True).first()
    return render_template('while_throwing.html',active_session=active_session)

@app.route('/after_throwing', methods=['GET', 'POST'])
@login_required
def after_throwing():
    # Retrieve the latest session for the current user
    last_session = Session.query.filter_by(user_id=current_user.id)\
        .order_by(Session.session_date.desc(), Session.end_time.desc())\
        .first()

    if not last_session:
        flash('No session data found.', 'warning')
        return redirect(url_for('home'))

    # Ensure the session has ended
    if last_session.active:
        flash('Session is still active.', 'warning')
        return redirect(url_for('home'))

    # Prepare data for the template
    template_data = {
        'count': last_session.trash_count,
        'current_user': current_user
    }

    return render_template('after_throwing.html', **template_data)

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
@login_requiredF
@admin_required
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
    if new_role == 'User':
        user.userlv = new_role
        db.session.commit()
    elif new_role == 'Admin':
        user.userlv = new_role
        db.session.commit()
    return redirect(url_for('manage_users'))

def get_coordinates(address):
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(address)
    if location:
        return (location.latitude, location.longitude)
    return None

@app.route('/update-location', methods=['POST'])
def update_location():
    data = request.get_json()
    if not data or 'latitude' not in data or 'longitude' not in data:
        return jsonify({'error': 'Location data required'}), 400

    try:
        user_coord = (float(data['latitude']), float(data['longitude']))
        bins = Bin.query.all()
        bin_distances = []

        for bin in bins:
            bin_coords = get_coordinates(bin.bin_location)
            if bin_coords:
                distance = geodesic(user_coord, bin_coords).kilometers
                bin_distances.append({
                    'bin_id': bin.bin_id,
                    'bin_type': bin.bin_type,
                    'location': bin.bin_location,
                    'distance': distance,
                    'is_full': bin.bin_full
                })

        ranked_bins = sorted(bin_distances, key=lambda x: x['distance'])

        return jsonify({
            'user_location': {'latitude': user_coord[0], 'longitude': user_coord[1]},
            'ranked_bins': ranked_bins
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/view-bins')
def view_bins_page():
    return render_template('nearest_bins.html')

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
        
        # Check if user already has an active session
        active_session = Session.query.filter_by(user_id=current_user.id, active=True).first()
        if active_session:
            return jsonify({'status': 'error', 'message': 'An active session already exists.'}), 400

        # Create a new session
        new_session = Session(
            user_id=current_user.id,
            bin_id=bin_id,
            session_date=datetime.now().date(),
            session_time=datetime.now().time(),
            trash_count=0,
            active=True
        )
        db.session.add(new_session)
        db.session.commit()
        
        
        return redirect(url_for('while_throwing'))

        """return jsonify({
            'message': 'Session started',
            'user_id': user_id,
            'bin_id': bin_id,
            'start_time': datetime.now().time().strftime(date_format)
        }), 200
    """
        
    except Exception as e:
        logging.error(f"Error in qrcode endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/detect')
def detect_submit():
    return render_template('detect_submit.html'), 200

# TODO just like qrcode need a button to console.log('detect') to take a picture in app and post
@app.route('/detect', methods=['POST'])
def detect_result():
    try:
        file = request.files['file']
        if file.mimetype == 'application/octet-stream':
            print('fuck me cant fix this')
        print(file)
        result = garbage_classification(file)
        print(result)
        return render_template('detect_result.html',result=result), 200

        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error in detect endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/manage_bins')
@login_required
@admin_required
def manage_bins():
    if request.method == 'POST':
        log_message()
    bins = Bin.query.all()
    return render_template('manage_bins.html', bins=bins)

@app.route('/update_bin', methods=['POST'])
def update_bin():
    try:
        # Get form data
        bin_id = request.form.get('bin_id')
        bin_type = request.form.get('bin_type')
        bin_location = request.form.get('bin_location')
        bin_full = request.form.get('bin_full') == 'on'

        # Validate required fields
        if not all([bin_id, bin_type, bin_location]):
            return jsonify({
                'success': False, 
                'error': 'All fields are required'
            }), 400

        # Find the bin
        bin_to_update = Bin.query.get(bin_id)

        if not bin_to_update:
            return jsonify({
                'success': False, 
                'error': 'Bin not found'
            }), 404

        # Update bin details
        bin_to_update.bin_type = bin_type
        bin_to_update.bin_location = bin_location
        bin_to_update.bin_full = bin_full

        # Commit changes
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Bin updated successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/add_new_bin', methods=['POST'])
def add_new_bin():
    try:
        # Extract form data
        bin_id = request.form.get('bin_id')
        bin_type = request.form.get('bin_type')
        bin_location = request.form.get('bin_location')
        bin_full = request.form.get('bin_full') == 'on'

        # Validate required fields
        if not all([ bin_type, bin_location]):
            return jsonify({
                'success': False, 
                'error': 'All fields are required'
            }), 400

        def generate_bin_id():
            while True:
                bin_id = random.randint(10000000, 99999999)
                existing_bin = Bin.query.filter_by(bin_id=bin_id).first()
                if not existing_bin:
                    return bin_id

        # Generate new bin ID
        new_bin_id = generate_bin_id()

        # Create new bin
        new_bin = Bin(
            bin_id=new_bin_id,
            bin_full=bin_full,
            bin_type=bin_type,
            bin_location=bin_location
        )
        
        db.session.add(new_bin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'New bin added successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500
    
@app.route('/delete_bin', methods=['POST'])
def delete_bin():
    try:
        bin_id = request.form.get('bin_id')

        if not bin_id:
            return jsonify({
                'success': False, 
                'error': 'Bin ID is required'
            }), 400

        bin_to_delete = Bin.query.get(bin_id)
        
        if not bin_to_delete:
            return jsonify({
                'success': False, 
                'error': 'Bin not found'
            }), 404

        db.session.delete(bin_to_delete)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Bin deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/personal_page')
@login_required
def personal_page():
    if request.method == 'POST':
        log_message()
    # Get all sessions for the current user
    user_sessions = Session.query.filter_by(user_id=current_user.id).all()
    bins = Bin.query.all()
    active_session = Session.query.filter_by(user_id=current_user.id, active=True).first()
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

    # ranking / achievement

    total_trash_achievement = {
        "Novice Recycler": 0,
        "Intermediate Recycler": 1,
        "Expert Recycler": 2,
        "Champion Recycler": 3,
        "Eco Warrior": 5,
    }
    user_ranking = "Novice Recycler"
    for ranking, min in total_trash_achievement.items():
        if total_trash >= min:
            user_ranking = ranking
    
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
        total_trash_achievement=total_trash_achievement,
        user_ranking = user_ranking,
        user_score=user_score,
        bins=bins,
        active_session=active_session,
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





@app.route('/start_session', methods=['POST'])
@login_required
def start_session():
    data = request.get_json()
    bin_id = data.get('bin_id')

    if not bin_id:
        return jsonify({'status': 'error', 'message': 'Bin ID is required.'}), 400

    # Check if user already has an active session
    active_session = Session.query.filter_by(user_id=current_user.id, active=True).first()
    if active_session:
        return jsonify({'status': 'error', 'message': 'An active session already exists.'}), 400

    # Fetch the selected bin from the database
    selected_bin = Bin.query.get(bin_id)
    if not selected_bin:
        return jsonify({'status': 'error', 'message': 'Bin not found.'}), 404

    # Check if the bin is full
    if selected_bin.bin_full:
        return jsonify({'status': 'error', 'message': 'Cannot start a session. The selected bin is full.'}), 400

    # Create a new session
    new_session = Session(
        user_id=current_user.id,
        bin_id=bin_id,
        session_date=datetime.now().date(),
        session_time=datetime.now().time(),
        trash_count=0,
        active=True
    )
    db.session.add(new_session)
    db.session.commit()

    return jsonify({'status': 'success', 'session_id': new_session.sessionid}), 200



@app.route('/end_session', methods=['POST'])
@login_required
def end_session():
    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'status': 'error', 'message': 'Session ID is required.'}), 400

    # Retrieve the active session
    session = Session.query.filter_by(sessionid=session_id, user_id=current_user.id, active=True).first()
    if not session:
        return jsonify({'status': 'error', 'message': 'Active session not found.'}), 404

    # End the session
    session.active = False
    session.end_time = datetime.now().time()
    start_datetime = datetime.combine(session.session_date, session.session_time)
    end_datetime = datetime.combine(session.session_date, session.end_time) if session.end_time else datetime.utcnow()
    session.time_used = end_datetime - start_datetime

    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Session ended successfully.'}), 200



@app.route('/update_trash_count', methods=['POST'])
def update_trash_count():
    data = request.get_json()
    session_id = data.get('session_id')
    trash_count = data.get('trash_count')

    if not session_id or trash_count is None:
        return jsonify({'status': 'error', 'message': 'Session ID and Trash Count are required.'}), 400

    # Retrieve the session regardless of its active status
    session = Session.query.filter_by(sessionid=session_id).first()
    if not session:
        return jsonify({'status': 'error', 'message': 'Session not found.'}), 404

    # Update trash count
    session.trash_count = trash_count
    db.session.commit()

    return jsonify({'status': 'success', 'trash_count': session.trash_count}), 200




@app.route('/get_active_session', methods=['GET'])
def get_active_session():
    bin_id = request.args.get('bin_id', type=int)

    if not bin_id:
        return jsonify({'status': 'error', 'message': 'Bin ID is required.'}), 400

    # Retrieve the active session for the given bin
    session = Session.query.filter_by(bin_id=bin_id, active=True).first()
    if session:
    # Access the username from the associated user
        username = session.user.username  # Assumes 'username' is a field in the User model
        return jsonify({
            'status': 'success',
            'session_id': session.sessionid,
            'username': username
        }), 200

    else:
        return jsonify({'status': 'error', 'message': 'No active session found for this bin.'}), 404

    #return jsonify({'status': 'success', 'session_id': session.sessionid,'username': username}), 200



@app.route('/get_bin_status', methods=['GET'])
def get_bin_status():
    bin_id = request.args.get('bin_id', type=int)
    if bin_id is None:
        return jsonify({'status': 'error', 'message': 'Bin ID is required.'}), 400

    bin = Bin.query.get(bin_id)
    if bin:
        return jsonify({'status': 'success', 'bin_full': bin.bin_full}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Bin not found.'}), 404
    


@app.route('/update_bin_status', methods=['POST'])
def update_bin_status():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Invalid JSON.'}), 400

    bin_id = data.get('bin_id')
    bin_full = data.get('binFull')

    if bin_id is None or bin_full is None:
        return jsonify({'status': 'error', 'message': 'Bin ID and binFull status are required.'}), 400

    bin = Bin.query.get(bin_id)
    if bin:
        bin.bin_full = bin_full
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Bin status updated.'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Bin not found.'}), 404




if __name__ == '__main__':
    app.run("0.0.0.0",port=5000,debug=True)