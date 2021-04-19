import os
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from flask import Flask

load_dotenv()

app = Flask(__name__)

app.config['ENV'] = 'development'
app.config['MONGODB_DB'] = os.environ.get('MONGODB_DB')
app.config['MONGODB_HOST'] = os.environ.get('MONGODB_HOST')
app.config['MONGODB_PORT'] = os.environ.get('MONGODB_PORT')
app.config['MONGODB_USERNAME'] = os.environ.get('MONGODB_USERNAME')
app.config['MONGODB_PASSWORD'] = os.environ.get('MONGODB_PASSWORD')
app.config['MONGO_URI'] = os.environ.get('MONGO_URI')

mongo_client = PyMongo(app)
db = mongo_client.db

from app import classes
from app import routes
