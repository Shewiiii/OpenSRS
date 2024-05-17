from app.manage_database import *
from datetime import datetime, timedelta, timezone
from app.model import Carte
from fsrs import *
from dateutil import tz


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
        srs_table = Constants.srs_table
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
    now = datetime.now()
    due_cards = {}
    for card in result:
        due = card[1]
        state = card[2]
        delta = due - now
        if delta <= timedelta(0):
            due_cards[card[0]] = {'due': due, 'state': state}
    due_cards = dict(sorted(due_cards.items(), key=lambda item: item[1]['due']))
    return list(due_cards.keys())
    

def get_due_cards_from_deck_id(
        deck_id: int,
        user_id: int = Constants.temp_user_id,
        srs_table = Constants.srs_table,
) -> list[int]:
    '''Retourne toutes les cartes dues d'un deck donnné. 
    '''
    cursor = db.query(f'SELECT card_id, due, state FROM {srs_table} '
                      f'WHERE deck_id = {deck_id} '
                      f'AND user_id = {user_id};')

    result = cursor.fetchall()
    due_cards = get_due_card_from_query(result)

    return due_cards


def get_due_cards_from_list(
    card_ids: list,
    deck_id: int,
    user_id: int = Constants.temp_user_id,
    srs_table = Constants.srs_table,
) -> list:
    '''Retourne toutes les cartes dues d'une liste d'ids donnée. 
    '''
    string = (f'SELECT card_id, due, state FROM {srs_table} '
              f'WHERE deck_id = {deck_id} '
              f'AND user_id = {user_id} AND ')
    
    for card_id in card_ids:
        string += f'card_id = {card_id} OR '
    string = f'{string[:-3]};'
    
    cursor = db.query(string)
    result = cursor.fetchall()
    due_cards = get_due_card_from_query(result)

    return due_cards


def rate_card(
    card_id: int,
    deck_id: int,
    user_id: int,
    rating: Rating,
    srs_table: str = Constants.srs_table,
    reviews_table: str = Constants.reviews_table,
) -> None:
    '''Ajoute une review dans la table reviews et replanifie une carte donnée.
    '''
    now = datetime.now(timezone.utc)
    #From db
    variables = get_card_variables(card_id, user_id)
    
    card = Carte()
    card.set_variables(variables)
    card.rate_debug(rating)
    #From class
    new_variables = card.get_variables()
    print(variables)
    print(new_variables)
    update_card_srs_from_dict(card_id, new_variables, user_id, srs_table=srs_table)
    
    state = int(card.card.state)
    timestamp = int(datetime.timestamp(now)*1000)
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
#POUR TESTS:
# from random import randint
# ids = get_all_ids()
# for id in ids:
#     for i in range(50):
#         add_review_entry(id, 0, 1, ['Again', 'Hard', 'Good', 'Easy'][randint(0,3)],1,1715977448081)

# ids = get_all_ids()
# for id in ids:
#     forget_card(id)
#for i in range(30):
#    create_card(deck_id=0)