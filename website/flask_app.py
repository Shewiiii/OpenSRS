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
        print(form.deck.data,form.front.data,form.front_sub.data,form.back.data,form.back_sub2.data,form.tag.data)
        create_card(id=get_free_id(),deck=form.deck.data,front=form.front.data,front_sub=form.front_sub.data,back=form.back.data,back_sub=form.back_sub.data,back_sub2=form.back_sub2.data,tag=form.tag.data)
        flash(f'La carte {form.front.data} a bien été enregistré dans le deck {form.deck.data} !')
        return redirect('/formtest')
    return render_template('form.html',title='Créer une carte',form=form)

@app.route('/decklist')

def decklist():
    return render_template('decklist.html', title='Liste de decks')






if __name__ == "__main__": #toujours à la fin!
    app.run(debug=True)