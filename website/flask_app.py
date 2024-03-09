from flask import Flask, render_template
from app.config import Config
from app.card_form import Cardform
app = Flask(__name__)
app.config.from_object(Config)
@app.route('/')

def index():
    return render_template('index.html')

@app.route('/home/<name>')

def home(name):
    return render_template('home.html', name=name)

@app.route('/formtest')

def cardform():
    form = Cardform()
    return render_template('form.html',title='Créer une carte !',form=form)








if __name__ == "__main__": #toujours à la fin!
    app.run(debug=True)