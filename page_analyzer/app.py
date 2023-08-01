from flask import Flask, request, render_template

app = Flask(__name__, template_folder='templates')

@app.route('/')
def handler():
    return render_template("index.html")
