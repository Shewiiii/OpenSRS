from app.manage_database import *
from datetime import datetime, timedelta, timezone
from app.model import Carte
from fsrs import *
from dateutil import tz
from random import randrange

db = DB()


def get_ratings_from_card_id(
        card_id: int,
        table: str = Constants.reviews_table,
) -> list[Rating]:
    '''(FSRS) Retourne les Rating d'une carte donnée. 
    '''
    ratings = []
    cursor = db.query(f'SELECT rating FROM {table} WHERE card_id = {card_id}')
    result = cursor.fetchall()

    if len(result) == 0:
        return []

    else:
        for row in result:
            ratings.append(Constants.rating_dict[row[0]])

        return ratings


def get_due_date_from_card_id(
        card_id: int,
        user_id: int = Constants.temp_user_id,
        srs_table=Constants.srs_table
) -> datetime:
    '''Retourne la date (datetime(timezone.utc)) due d'une carte donnée.
    '''
    cursor = db.query(f'SELECT due FROM {srs_table} '
                      f'WHERE card_id = {card_id} '
                      f'AND user_id = {user_id};')
    result = cursor.fetchall()

    if len(result) == 0:
        return None

    else:
        return result[0][0].replace(tzinfo=timezone.utc)


def get_due_card_from_query(result: list):
    '''Retourne les cartes dues à partir du résultat d'une requête SQL.
        Organise et trie de plus cette dernière. 
    '''
    now = datetime.now()
    due_cards = {}
    for card in result:
        due = card[1]
        delta = due - now
        if delta <= timedelta(0):
            due_cards[card[0]] = due
    due_cards = dict(sorted(due_cards.items(), key=lambda item: item[1]))
    return list(due_cards.keys())


def get_due_cards_from_deck_id(
        deck_id: int,
        user_id: int = Constants.temp_user_id,
        srs_table=Constants.srs_table,
) -> list[int]:
    '''Retourne toutes les cartes dues d'un deck donnné. 
    '''
    cursor = db.query(f'SELECT card_id, due FROM {srs_table} '
                      f'WHERE deck_id = {deck_id} '
                      f'AND user_id = {user_id};')

    result = cursor.fetchall()
    due_cards = get_due_card_from_query(result)

    return due_cards


def get_due_cards_from_list(
    card_ids: list,
    deck_id: int,
    user_id: int = Constants.temp_user_id,
    srs_table=Constants.srs_table,
) -> list:
    '''Retourne toutes les cartes dues d'une liste d'ids donnée. 
    '''
    string = (f'SELECT card_id, due FROM {srs_table} '
              f'WHERE deck_id = {deck_id} '
              f'AND user_id = {user_id} AND ')

    for card_id in card_ids:
        string += f'card_id = {card_id} OR '
    string = f'{string[:-3]};'

    cursor = db.query(string)
    result = cursor.fetchall()
    due_cards = get_due_card_from_query(result)

    return due_cards


def get_cards_srs_to_review(
        deck_id: int,
        new_cards_mode: str = 'end',
        new_cards_limit: int = 10,
        srs_table=Constants.srs_table,
) -> dict:
    '''Renvoie la liste des cartes srs à review dans un deck donné.
        La quantité et l'emplacement des nouvelles cartes peut être précisé.

        Modes possibles: 'start', 'end' (par défaut), 'shuffle'.
    '''
    cards_srs = get_cards_srs_from_deck_id(deck_id, table=srs_table)
    now = datetime.now()
    due_dict = {}
    new_cards = []
    new_cards_count = 0
    for card_srs in cards_srs:
        due = card_srs['due']
        delta = due - now
        if delta <= timedelta(0):

            new_card = card_srs['state'] == 0
            if new_card:
                if new_cards_count < new_cards_limit:
                    new_cards_count += 1
                    new_cards.append(card_srs)

            else:
                due_dict[card_srs['due']] = card_srs

    due_cards = list(
        dict(sorted(due_dict.items())).values()
    )

    if new_cards_mode == 'start':
        due_cards = new_cards + due_cards

    elif new_cards_mode == 'end':
        due_cards += new_cards

    elif new_cards_mode == 'shuffle':
        for card_id in new_cards:
            due_cards.insert(randrange(len(due_cards)+1), card_id)

    return due_cards


def rate_card(
    card_id: int,
    deck_id: int,
    user_id: int,
    rating: Rating,
    srs_table: str = Constants.srs_table,
) -> State:
    '''Ajoute une review dans la table reviews et replanifie une carte donnée.
    '''
    now = datetime.now(timezone.utc)
    # From db
    variables = get_card_variables(card_id)

    card = Carte()
    card.set_variables(variables)
    og_state = int(card.card.state)
    card.rate_debug(rating)
    # From class
    new_variables = card.get_variables()
    update_card_srs_from_dict(card_id, new_variables,
                              srs_table=srs_table)

    state = int(card.card.state)
    timestamp = int(datetime.timestamp(now))
    dico = {
        Rating.Again: 'Again',
        Rating.Hard: 'Hard',
        Rating.Good: 'Good',
        Rating.Easy: 'Easy',
    }
    add_review_entry(
        card_id,
        deck_id,
        user_id,
        dico[rating],
        state,
        timestamp,
    )

    return og_state


def get_review_stats_from_deckid(
    deck_id: int,
    new_cards_mode: str = 'shuffle',
    new_cards_limit: int = Constants.new_cards_limit,
) -> dict:
    '''Retourne le nombre de cartes à revoir et nouvelles. 
    '''
    due_cards_srs = get_cards_srs_to_review(
        deck_id,
        new_cards_mode,
        new_cards_limit,
    )
    new_cards_remaining = 0
    for card in due_cards_srs:
        if card['state'] == 0:
            new_cards_remaining += 1
    review_cards_count = len(due_cards_srs) - new_cards_remaining

    stats = {
        'review': review_cards_count,
        'new': new_cards_remaining
    }

    return stats


def dt(timestamp: int) -> datetime:
    '''Convertit un timestamp en datetime utc.
    '''
    date = datetime.fromtimestamp(timestamp)
    date = date.replace(tzinfo=timezone.utc)

    return date


def get_fsrs_from_reviews(
    card_id: int,
    user_id: int,
    reviews: list,
    params: tuple = Constants.default_params,
    retention: int = Constants.default_retention,
    get_reviews: bool = False,
    deck_id: int | None = None,
    rating_dict: dict = Constants.rating_dict,
    rating_key: str = 'rating'
) -> dict | tuple[dict, list]:
    '''Récupère les variables FSRS en fonction d'un dictionnaire de reviews.

       La variable "rating" est là car les clés dans le dico n'ont pas
       les mêmes noms entre OpenSRS et jpdb (cursed).

       Si add_review == True, l'id du deck doit être précisé.
    '''
    card_reviews = []

    first_review = dt(reviews[0]['timestamp'])
    card_srs = Carte(
        created=first_review,
        params=params,
        retention=retention,
    )

    for review in reviews:
        timestamp = review['timestamp']
        date = dt(timestamp)
        try:
            rating = rating_dict[review[rating_key]]
            card_srs.rate(rating, now=date)
            if get_reviews:
                card_review = {
                    'card_id': card_id,
                    'deck_id': deck_id,
                    'user_id': user_id,
                    'rating': rating,
                    'timestamp': timestamp,
                    'state': -1,
                }
                card_reviews.append(card_review)
        except Exception as e:
            print('Error', e)
    variables = card_srs.get_variables()
    if get_reviews:
        return variables, card_reviews
    else:
        return variables


def reschedule_cards(
    deck_id: int,
    user_id: int = Constants.temp_user_id,
    params: tuple = Constants.default_params,
    retention: int = Constants.default_retention
) -> None:
    '''Replanifie les cartes d'un deck. 
       Utile après avoir modifié la rétention ou les paramètres FSRS.
    '''
    ar = get_reviews_from_deck_id(deck_id)
    card_reviews = {}
    # Contient en clé un card_id et en valeur ses reviews
    for review in ar:
        card_id = review['card_id']
        if card_id in card_reviews:
            card_reviews[card_id].append(review)
        else:
            card_reviews[card_id] = [review]

    cards_variables = {}
    for card_id, reviews in card_reviews.items():
        variables = get_fsrs_from_reviews(
            card_id,
            user_id,
            reviews,
            params=params,
            retention=retention,
        )
        cards_variables[card_id] = variables

    bulk_update_cards_srs(cards_variables)


# POUR TESTS:
# from random import randint
# ids = get_all_ids()
# for id in ids:
#     for i in range(50):
#         add_review_entry(id, 0, 1, ['Again', 'Hard', 'Good', 'Easy'][randint(0,3)],1,1715977448081)

# ids = get_all_ids()
# for id in ids:
#     forget_card(id)

# for i in range(30):
#    create_card(deck_id=0)
