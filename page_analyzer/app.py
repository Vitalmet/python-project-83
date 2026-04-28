from flask import Flask


app = Flask(__name__)




@app.route("/")
def index():
   return "Анализатор страниц приветствует тебя!"

@app.route("/analyze")
def analyze():
   return {"статус": "готов", "сообщене": "Анализатор страниц работает!"}