'''Define the routes and views for the web pages.'''
from flask import Blueprint, render_template

bp = Blueprint('pages', __name__)

@bp.route('/')
def home():
    return render_template('pages/home.html') # render_template will look for the file in the templates folder

@bp.route('/werx')
def werx():
    return render_template('pages/werx.html')

@bp.route('/contact')
def contact():
    return render_template('pages/contact.html')