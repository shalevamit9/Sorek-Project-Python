from flask import Flask

app = Flask(__name__)
app.config['ENV'] = 'development'

from app import routes
from app import classes
