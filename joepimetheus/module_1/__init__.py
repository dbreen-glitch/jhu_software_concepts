from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def base():
    return render_template('base.html') # render_template will look for the file in the templates folder

@app.route('/works')
def projects():
    return render_template('works.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__=='__main__':
    app.run(host='0.0.0.0', port=8080)
