from flask import Flask

webapp = Flask(__name__)

@webapp.route('/', methods = ['GET'])
def index():
	return 'Hello'