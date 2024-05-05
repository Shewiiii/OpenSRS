from flask import Flask, render_template, flash, redirect
from app.config import Config
from app.card_form import Cardform
from app.manage_database import *

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/')

def index():
    return render_template('index.html')

@app.route('/home/<name>')

def home(name):
    return render_template('home.html', name=name)

@app.route('/formtest', methods=['GET', 'POST'])

def cardform():
    form = Cardform()
    if form.validate_on_submit():
        deckid = form.deckid
        front = form.front
        front_sub = form.front_sub
        back = form.back
        back_sub = form.back_sub
        back_sub2 = form.back_sub2
        tag = form.tag
        create_card(deckid, front, front_sub, back, back_sub, back_sub2, tag, user_id=1)
        flash(f'La carte {form.front.data} a bien été enregistré dans le deck {form.deckid.data} !')
        return redirect('/formtest')
    return render_template('form.html',title='Créer une carte',form=form)

@app.route('/decklist')

def decklist():
    return render_template('decklist.html', title='Liste de decks')






if __name__ == "__main__": #toujours à la fin!
    app.run(debug=True)