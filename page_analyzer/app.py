import os
from dotenv import load_dotenv
from flask import Flask

#загружаем переменные окружения из .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-dev')



@app.route("/")
def index():
   return "Анализатор страниц приветствует тебя!"

@app.route("/analyze")
def analyze():
   return {"статус": "готов", "сообщене": "Анализатор страниц работает!"}