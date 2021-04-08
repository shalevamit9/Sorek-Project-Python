import os
from flask_mongoengine import MongoEngine
from flask import Flask

app = Flask(__name__)
app.config['ENV'] = 'development'
# app.config['MONGODB_DB'] = os.environ.get('MONGODB_DB')
# app.config['MONGODB_HOST'] = os.environ.get('MONGODB_HOST')
# app.config['MONGODB_PORT'] = os.environ.get('MONGODB_PORT')
# app.config['MONGODB_USERNAME'] = os.environ.get('MONGODB_USERNAME')
# app.config['MONGODB_PASSWORD'] = os.environ.get('MONGODB_PASSWORD')
#
# db = MongoEngine(app)


from app import classes
# from app import models
from app import routes
