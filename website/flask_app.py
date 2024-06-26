from flask import Flask, render_template, flash, redirect, request, session, make_response
from app.config import Config
from app.card_form import Cardform
from app.deck_form import Deckform
from app.deck_settings import Decksettings
from app.manage_database import *
from app.reviews import *
from datetime import datetime, timedelta
import pathlib
import os
from threading import Thread


app = Flask(__name__)
app.config.from_object(Config)

t = Thread(target=update_users)
# t.start()


def legit(request, user_id):
    '''Vérifie qu'il s'agit du propriétaire du deck qui cherche à l'accéder.
    '''
    sid = request.cookies.get('SID')
    c_user_id = get_user_id(sid)
    
    return c_user_id == user_id


@app.route('/')
def index():
    
    sid = request.cookies.get('SID')
    if sid:
        return redirect('/decklist')
    return render_template('index.html')


@app.route('/home/<name>')
def home(name):
    
    return render_template('home.html', name=name)


@app.route('/decklist')
def decklist():
    
    sid = request.cookies.get('SID')
    if not sid:
        return redirect('/')
    user_id = get_user_id(sid)
    decks = get_decks_from_user(user_id=user_id)
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
def deck_page(deck_id):

    # Gestion des pages:
    page = request.args.get('page', type=int)
    if page == None:
        page_change = False
        page = 1
        offset = 0
    else:
        page_change = True
        offset = page*50-50

    # Gestion de la recherche:
    search = request.args.get('search', type=str)
    if search == None:
        search = ''

    deck_info, cards = get_deck_from_id(
        deck_id,
        show=50,
        offset=offset,
        search=search,
    )

    if not legit(request, deck_info['user_id']):
        return "Qu'essayes-tu de faire ? :)"

    page_count = deck_info['card_count']//50+1

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
        title=deck_info['name'],
        deck_info=deck_info,
        cards=cards,
        img_id=img_id,
        extension=extension,
        offset=offset,
        page_change=page_change,
        page=page,
        page_count=page_count,
        search=search
    )


@app.route('/deck/<deck_id>/settings', methods=['GET', 'POST'])
def deck_settings(deck_id):
    
    deck_id = int(deck_id)
    form = Decksettings()
    deck = get_deck_from_id(deck_id, show=1)[0]

    if not legit(request, deck['user_id']):
        return 'Nope'

    name = deck['name']
    description = deck['description']
    params = eval(deck['params'])
    retention = float(deck['retention'])

    if form.validate_on_submit():
        d = form.data

        name = d['name']
        description = d['description']

        u_params = eval(d['params'])
        u_retention = float(d['retention'])

        if (params != u_params 
            or retention != u_retention):

            params = u_params
            retention = u_retention

            reschedule_cards(
                deck_id,
                params=params,
                retention=retention
            )

        new_values = {
            'name': name,
            'description': description,
            'params': params,
            'retention': retention,
        }

        update_deck(deck_id, new_values)
        flash('Le deck a bien été modifié !')
        deck = get_deck_from_id(deck_id, show=0)[0]

    return render_template(
        'deckSettings.html',
        title='Paramètres du deck',
        deck_id=deck_id,
        name=name,
        description=description,
        params=params,
        retention=retention,
        form=form,
    )


@app.route('/deck/<deck_id>/add', methods=['GET', 'POST'])
def cardform(deck_id):
    
    form = Cardform()
    deck = get_deck_from_id(deck_id, show=0)[0]
    
    user_id = get_user_id(request.cookies.get('sid'))
    if not legit(request, deck['user_id']):
        return 'Nope'

    name = deck['name']

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
            user_id=user_id,
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
    
    deck = get_deck_from_id(deck_id, show=0)[0]
    if not legit(request, deck['user_id']):
        return 'Nope'
    
    name = deck['name']

    return render_template(
        'deleteDeck.html',
        title=f'Supprimer {name}',
        deck_id=deck_id,
    )


@app.route('/deck/<deck_id>/delete/confirm', methods=['GET', 'POST'])
def confirm_delete(deck_id):
    
    deck = get_deck_from_id(deck_id, show=0)[0]
    if not legit(request, deck['user_id']):
        return 'Nope'
    
    delete_deck(deck_id)
    response = make_response(redirect('/decklist'))
    response.set_cookie(f'NEW_CARDS_COUNT{deck_id}', '', expires=0)

    return response


@app.route('/addDeck', methods=['GET', 'POST'])
def deckform():
    
    sid = request.cookies.get('SID')
    user_id = get_user_id(sid)

    form = Deckform()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data

        create_deck(name=name,
                    description=description,
                    user_id=user_id)
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
    refresh_deck_session(deck_id)
    new_cards_remaining = get_new_cards_remaining(deck_id)

    due_cards_srs = get_cards_srs_to_review(
        deck_id,
        new_cards_mode=Constants.new_cards_mode,
        new_cards_limit=new_cards_remaining,
    )
    due_count = len(due_cards_srs)

    # choisit carte à review:
    if due_count == 0:
        card = None
    else:
        card_id = due_cards_srs[0]['card_id']
        card = get_card_from_card_id(card_id)

    # ajoute des stats: get_stats(due_cards_srs)
    stats = get_review_stats_from_deckid(
        deck_id=deck_id,
        new_cards_limit=new_cards_remaining,
    )
    new_cards_remaining = stats['new']
    review_cards_remaining = stats['review']

    # réponse:
    return render_template(
        'review.html',
        title='Review',
        card=card,
        new=new_cards_remaining,
        review=review_cards_remaining,

    )


@app.route('/deck/<deck_id>/review/<card_id>/<rating>')
def rate(deck_id, card_id, rating):
    
    user_id = get_user_id(request.cookies.get('SID'))
    
    rating = Constants.rating_dict[rating]
    state = rate_card(
        card_id,
        deck_id,
        user_id,
        rating,
    )

    if state == State.New:
        new_cards_remaining = get_new_cards_remaining(deck_id)
        if new_cards_remaining >= 1:
            decrease_new_cards_remaining(deck_id, number=1)

    return redirect(f'/deck/{deck_id}/review')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']
        user_id = test_login(username, password)
        # None si connection échouée, user_id sinon

        if user_id != None:
            # Générer un SID
            sid = init_user(user_id)

            response = make_response(redirect('/decklist'))
            response.set_cookie('SID', sid,
                                expires=datetime.now() + timedelta(days=30))
            response.set_cookie('CONNECTED', 'True',
                                expires=datetime.now() + timedelta(days=30))
            response.set_cookie('USERNAME', username,
                                expires=datetime.now() + timedelta(days=30))
            response.set_cookie('PASSWORD', password,
                                expires=datetime.now() + timedelta(days=30))

            return response

        else:
            flash('Identifiant ou mot de passe incorrect.')

    return render_template('login.html', title='Connection')


@app.route('/logout')
def logout():
    
    response = make_response(redirect('/login'))

    response.set_cookie('SID', '', expires=0)
    return response


@app.route('/register', methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if user_exists(username):
            flash("Nom d'utilisateur ou email déjà utilisé")

        else:
            add_login(username, password)
            flash("Compte créé ! Vous pouvez maintenant vous connecter.")
            return redirect('/login')

    return render_template('register.html', title='Créer un compte', not_new=False)


if __name__ == "__main__":  # toujours à la fin!
    app.run(debug=True)
