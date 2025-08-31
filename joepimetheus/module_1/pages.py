from flask import Blueprint, render_template

bp = Blueprint('pages', __name__)

@bp.route('/')
def home():
    return render_template('pages/home.html') # render_template will look for the file in the templates folder

@bp.route('/works')
def works():
    return render_template('pages/works.html')

@bp.route('/contact')
def contact():
    return render_template('pages/contact.html')