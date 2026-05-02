import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash

#загружаем переменные окружения из .env
load_dotenv()

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__,template_folder=template_dir)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key-for-dev')



@app.route("/")
def index():
   return render_template('index.html')

@app.route("/chek", methods=['POST'])
def chek_url():
   url = request.form.get('url', '').strip()

   if not url:
      flash('URL не может быть пустым', 'danger')
      return redirect(url_for('index'))

   if not url.startswith(('http://', 'https://')):
      flash('URL должен начинаться с http:// или https://', 'danger')
      return redirect(url_for('index'))

   flash(f'Анализ страницы {url} начат', 'success')
   return redirect(url_for('index'))

if __name__ == "__main__":
   app.run(debug=True)
