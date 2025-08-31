from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')

def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return "This is the about page."

@app.route('/contact')
def contact():
    return "For more information contact Dylan."


if __name__=='__main__':
    app.run(host='0.0.0.0', port=8080)
