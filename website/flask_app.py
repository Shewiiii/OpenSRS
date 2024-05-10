from flask import Flask, render_template, flash, redirect,request
from app.config import Config
from app.card_form import Cardform
from app.deck_form import Deckform
from app.manage_database import *
from app.manage_database import *
import pathlib
import os


app = Flask(__name__)
app.config.from_object(Config)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/home/<name>')
def home(name):
    return render_template('home.html', name=name)


@app.route('/decklist')
def decklist():
    decks = get_decks_from_user(user_id=1)
    '''Exemple:
    [{
        'deck_id': 0,
        'name': 'keqing',
        'description': 'yes',
        'created': datetime.datetime(2024, 5, 10, 14, 21, 55),
        'card_count': 2,
        'img_id': 0,
        'extension': '.jpg'
    }]
    '''

    return render_template('decklist.html', title='Liste de decks', decks=decks)


@app.route('/deck/<deck_id>')
def deckPage(deck_id):
    deckInfo, cards = get_deck_from_id(deck_id, Constants.temp_user_id)
    '''Exemple de deck:
    ({'deck_id': 0,
      'name': 'name',
      'description': 'description',
      'created': datetime.datetime(2024, 5, 6, 0, 33, 4)},

    [{'card_id': 1,
      'front': 'je suis un front',
      'front_sub': 'sous front',
      'back': 'bacc',
      'back_sub': 'sub bacc',
      'back_sub2': 'sub bacc 2',
      'tag': 'uwu'},
    {'card_id': 2,
      'front': 'oezjtoerjitger',
      'front_sub': 'front_sub',
      'back': 'back',
      'back_sub': 'back_sub',
      'back_sub2': 'back_sub2',
      'tag': 'tag'}])
    '''
    img_id, extension = get_img(deck_id)

    return render_template('deck.html', title=deckInfo['name'],deckInfo=deckInfo, cards=cards, img_id=img_id, extension=extension)


@app.route('/deck/<deck_id>/add', methods=['GET', 'POST'])
def cardform(deck_id):
    form = Cardform()
    name = get_deck_from_id(deck_id,1)[0]['name']
    if form.validate_on_submit():
        front = form.front.data
        front_sub = form.front_sub.data
        back = form.back.data
        back_sub = form.back_sub.data
        back_sub2 = form.back_sub2.data
        tag = form.tag.data
        create_card(deck_id, front, front_sub, back,
                    back_sub, back_sub2, tag, user_id=1)
        flash(f'La carte {front} a bien été enregistré dans le deck {name} !')
        return redirect(f'/deck/{deck_id}/add')
    return render_template('addCard.html', title='Créer une carte', form=form, name=name, deck_id=deck_id)


@app.route('/deck/<deck_id>/delete')
def delete(deck_id):
    name = get_deck_from_id(deck_id,1)[0]['name']
    return render_template('deleteDeck.html', title=f'Supprimer {name}', deck_id=deck_id)


@app.route('/deck/<deck_id>/delete/confirm', methods=['GET', 'POST'])
def confirmDelete(deck_id):
    delete_deck(deck_id)
    return redirect('/decklist')


@app.route('/addDeck', methods=['GET', 'POST'])
def deckform():
    form = Deckform()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data

        create_deck(name=name, description=description)
        return redirect('/decklist')
    return render_template('addDeck.html', title='Créer un deck', form=form)

@app.route('/deck/<deck_id>', methods=['GET', 'POST'])
def changeImg(deck_id):
    if request.method == 'POST':
        f = request.files['image']
        filename = f.filename
        extension = os.path.splitext(filename)[1]

        img_id = add_image(deck_id, extension)
        path = pathlib.Path(__file__).parents[0] / 'static/img/uploads' / f'{img_id}{extension}'
        
        f.save(path)
        return redirect(f'{deck_id}')


if __name__ == "__main__":  # toujours à la fin!
    app.run(debug=True)
