from flask import request, jsonify, render_template, flash, redirect, url_for, session as flask_session
from datetime import datetime, timedelta
from config import app, bcrypt, db  # Import the already initialized app
from model import User, Session, Leaderboard, Bin

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not all(key in data for key in ['username', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400
        
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400
        
    new_user = User(username=data['username'], user_password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully', 'userid': new_user.userid}), 201

@app.route('/start_session', methods=['POST'])
def start_session():
    data = request.get_json()
    
    if not all(key in data for key in ['userid', 'bin_id']):
        return jsonify({'error': 'Missing required fields'}), 400
        
    user = User.query.get(data['userid'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    bin = Bin.query.get(data['bin_id'])
    if not bin:
        return jsonify({'error': 'Bin not found'}), 404
    
    new_session = Session(
        userid=data['userid'],
        bin_id=data['bin_id'],
        time_of_usage=datetime.now(),
        time_used=timedelta(seconds=0)
    )
    
    db.session.add(new_session)
    user.session_count += 1
    db.session.commit()
    
    return jsonify({'message': 'Session started', 'sessionid': new_session.sessionid}), 201


@app.route('/end_session/<int:session_id>', methods=['PUT'])
def end_session(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    session.time_used = datetime.now() - session.time_of_usage
    db.session.commit()
    
    return jsonify({'message': 'Session ended', 'time_used': str(session.time_used)}), 200

@app.route('/update_bin/<int:bin_id>', methods=['PUT'])
def update_bin(bin_id):
    data = request.get_json()
    bin = Bin.query.get(bin_id)
    
    if not bin:
        return jsonify({'error': 'Bin not found'}), 404
    
    if 'bin_full' in data:
        bin.bin_full = data['bin_full']
    
    db.session.commit()
    return jsonify({'message': 'Bin updated successfully'}), 200

@app.route('/leaderboard')
def get_leaderboard():
    leaderboard = Leaderboard.query.order_by(Leaderboard.user_score.desc()).all()
    results = []
    for entry in leaderboard:
        results.append({
            'username': entry.user.username,
            'score': entry.user_score
        })
    return jsonify({'leaderboard': results})

@app.route('/user_stats/<int:user_id>')
def get_user_stats(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    stats = {
        'username': user.username,
        'session_count': user.session_count,
        'score': user.leaderboard_entry.user_score if user.leaderboard_entry else 0,
        'total_trash': sum(session.trash_count for session in user.sessions)
    }
    return jsonify(stats)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        user = User.query.filter_by(username=data['username']).first()
        
        if user and bcrypt.check_password_hash(user.user_password, data['password']):
            flask_session['user_id'] = user.userid
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        
        if data['password'] != data['confirm_password']:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
            
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            flash('Username already exists!', 'error')
            return render_template('register.html')
            
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        new_user = User(username=data['username'], user_password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
def logout():
    flask_session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)