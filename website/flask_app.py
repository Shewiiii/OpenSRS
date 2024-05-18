from flask import Flask, render_template, flash, redirect, request, session, make_response
from app.config import Config
from app.card_form import Cardform
from app.deck_form import Deckform
from app.manage_database import *
from app.reviews import *
from datetime import datetime, timedelta
import re
import pathlib
import os
import json
import pendulum


app = Flask(__name__)
app.config.from_object(Config)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '!nxbTjiPw7@Pb8'
app.config['MYSQL_DB'] = 'cards'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/home/<name>')
def home(name):
    return render_template('home.html', name=name)


@app.route('/decklist')
def decklist():
    decks = get_decks_from_user(request, user_id=1)
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
    
    response = make_response(render_template(
        'decklist.html', title='Liste de decks', decks=decks))

    return response


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

    return render_template(
        'deck.html',
        title=deckInfo['name'],
        deckInfo=deckInfo,
        cards=cards,
        img_id=img_id,
        extension=extension
    )


@app.route('/deck/<deck_id>/add', methods=['GET', 'POST'])
def cardform(deck_id):
    form = Cardform()
    name = get_deck_from_id(deck_id, 1)[0]['name']

    if form.validate_on_submit():
        front = form.front.data
        front_sub = form.front_sub.data
        back = form.back.data
        back_sub = form.back_sub.data
        back_sub2 = form.back_sub2.data
        tag = form.tag.data

        create_card(
            deck_id,
            None,
            front,
            front_sub,
            back,
            back_sub,
            back_sub2,
            tag,
            user_id=1,
        )
        flash(f'La carte {front} a bien été enregistré dans le deck {name} !')

        return redirect(f'/deck/{deck_id}/add')

    return render_template(
        'addCard.html',
        title='Créer une carte',
        form=form,
        name=name,
        deck_id=deck_id,
    )


@app.route('/deck/<deck_id>/delete')
def delete(deck_id):
    name = get_deck_from_id(deck_id, 1)[0]['name']

    return render_template(
        'deleteDeck.html',
        title=f'Supprimer {name}',
        deck_id=deck_id,
    )


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

    return render_template(
        'addDeck.html',
        title='Créer un deck',
        form=form)


@app.route('/deck/<deck_id>', methods=['GET', 'POST'])
def changeImg(deck_id):
    if request.method == 'POST':
        f = request.files['image']
        filename = f.filename
        extension = os.path.splitext(filename)[1]

        img_id = add_image(deck_id, extension)
        path = pathlib.Path(
            __file__).parents[0] / 'static/img/uploads' / f'{img_id}{extension}'

        f.save(path)

        return redirect(f'{deck_id}')


@app.route('/deck/<deck_id>/<card_id>/delete', methods=['GET', 'POST'])
def deleteCard(card_id, deck_id):
    delete_card(card_id)

    return redirect(f'/deck/{deck_id}')


@app.route('/deck/<deck_id>/review')
def review(deck_id):
    # gère limite de nouvelles cartes:
    if f'NEW_CARDS_COUNT{deck_id}' in request.cookies:
        new_cards_count = int(request.cookies.get(f'NEW_CARDS_COUNT{deck_id}'))
        first_review = False

    else:
        new_cards_count = 0
        first_review = True

    due_cards_srs = get_cards_srs_to_review_from_deck_id(
        deck_id,
        new_cards_mode=Constants.new_cards_mode,
        new_cards_limit=Constants.new_cards_limit - new_cards_count,
    )
    due_count = len(due_cards_srs)

    # choisit carte à review:
    if due_count == 0:
        card = None
    else:
        card_id = due_cards_srs[0]['card_id']
        card = get_card_from_card_id(card_id)

    # ajoute des stats: get_stats(due_cards_srs)
    stats = get_review_stats(due_cards_srs)
    new_cards_remaining = stats['new']
    review_cards_remaining = stats['review']

    # réponse:
    response = make_response(render_template(
        'review.html',
        title='Review',
        card=card,
        new=new_cards_remaining,
        review=review_cards_remaining,
            
    ))
    if first_review:
        response.set_cookie(
            f'NEW_CARDS_COUNT{deck_id}',
            '0',
            expires=pendulum.tomorrow(Constants.timezone),
        )

    return response


@app.route('/deck/<deck_id>/review/<card_id>/<rating>')
def rate(deck_id, card_id, rating):
    rating = Constants.rating_dict[rating]
    state = rate_card(card_id, deck_id, Constants.temp_user_id, rating)
    
    if state == State.New:
        print('gneb drfothrdtlnitip')
        response = make_response(redirect(f'/deck/{deck_id}/review'))
        new = int(request.cookies.get(f'NEW_CARDS_COUNT{deck_id}'))
        response.set_cookie(f'NEW_CARDS_COUNT{deck_id}',
                           str(new + 1),
                           expires=datetime.now() + timedelta(days=30))
        return response

    else:
        return redirect(f'/deck/{deck_id}/review')


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = 'bouh'
    print(request.form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        """ hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode()) # encode le password
        password = hash.hexdigest()"""

        testLogin = test_login(username, password)
        # None si connection échouée, user_id sinon

        if testLogin != None:
            response = make_response(redirect('/decklist'))
            response.set_cookie('USER_id', testLogin,
                                expires=datetime.now() + timedelta(days=30))
            response.set_cookie('CONNECTED', 'True',
                                expires=datetime.now() + timedelta(days=30))
            response.set_cookie('USERNAME', username,
                                expires=datetime.now() + timedelta(days=30))
            response.set_cookie('PASSWORD', password,
                                expires=datetime.now() + timedelta(days=30))

            return response

        else:
            msg = 'username ou mot de passe incorrect'

    return render_template('login.html', title='Connexion'+msg, msg=msg)


@app.route('/logout')
def logout():
    response = make_response(redirect('/login'))

    response.set_cookie('USER_ID', '', expires=0)
    response.set_cookie('CONNECTED', '', expires=0)
    response.set_cookie('USERNAME', '', expires=0)
    response.set_cookie('PASSWORD', '', expires=0)

    return redirect('/login')

# @app.route('/register')
# def register():
#     msg = ''
#     if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
#         username = request.form['username']
#         password = request.form['password']
#         email = request.form['email']

#         cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#         cursor.execute('SELECT * FROM cards WHERE username = %s', (username,))
#         account = cursor.fetchone()

#         if account:
#             msg = 'Compte déjà existant'
#         elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
#             msg = 'Adresse mail invalide'
#         elif not re.match(r'[A-Za-z0-9]+', username):
#             msg = "L'identifiant ne comptenir que des lettres et des nombres"
#         elif not username or not password or not email:
#             msg = 'Veuillez remplir les champs manquants'
#         else:
#             '''hash = password + app.secret_key
#             hash = hashlib.sha1(hash.encode())
#             password = hash.hexdigest()'''
#             cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
#             mysql.connection.commit()
#             msg = 'Compte crée avec succès !'
#     elif request.method == 'POST':
#         msg = 'Veuillez remplir les champs manquants'

#     return render_template('/', msg=msg)


if __name__ == "__main__":  # toujours à la fin!
    app.run(debug=True)
