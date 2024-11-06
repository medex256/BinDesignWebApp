from config import db 

class User(db.Model):
    userid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    user_password = db.Column(db.String(100), nullable=False)
    session_count = db.Column(db.Integer, default=0)
    userlv = db.Column(db.Integer, default=0) 
    sessions = db.relationship('Session', backref='user', lazy='dynamic')
    leaderboard_entry = db.relationship('Leaderboard', backref='user', uselist=False)
    

class Session(db.Model):
    sessionid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False)
    time_of_usage = db.Column(db.DateTime, nullable=False)
    time_used = db.Column(db.Interval, nullable=False)
    bin_id = db.Column(db.Integer, db.ForeignKey('bin.bin_id'), nullable=False)
    trash_count = db.Column(db.Integer, default=0)

class Leaderboard(db.Model):
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), primary_key=True)
    user_score = db.Column(db.Integer, default=0)

class Bin(db.Model):
    bin_id = db.Column(db.Integer, primary_key=True)
    bin_full = db.Column(db.Boolean, default=False)
    bin_type = db.Column(db.String(50), nullable=False)
    sessions = db.relationship('Session', backref='bin', lazy='dynamic')
pass 