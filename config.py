from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

# Create the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smart_bin.db'
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Add a secret key

# Initialize extensions
db = SQLAlchemy(app)  # Initialize directly with app
bcrypt = Bcrypt(app)  # Initialize directly with app