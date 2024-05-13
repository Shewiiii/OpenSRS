from app.manage_database import *
from datetime import datetime, timedelta, UTC
from app.model import Carte
from fsrs import *
db = DB()



def get_ratings_from_card_id(card_id: int, table=Constants.reviews_table) -> list[Rating] | None:
    '''(FSRS) Retourne les Rating d'une carte donnée. 
    '''
    ratings = []
    cursor = db.query(f'SELECT rating FROM {table} WHERE card_id = {card_id}')
    result = cursor.fetchall()
    if len(result) == 0:
        return None
    else:
        dico = {'Again': Rating.Again, 'Hard': Rating.Hard, 'Good': Rating.Good, 'Easy': Rating.Easy}
        for row in result:
            ratings.append(dico[row[0]])
        return ratings


def get_due_date_from_card_id(card_id: int, user_id: int = Constants.temp_user_id, card_table = Constants.cards_table) -> datetime:
    '''Retourne la date (datetime(UTC)) due d'une carte donnée.
    '''
    cursor = db.query(f'SELECT created FROM {card_table} WHERE card_id = {card_id} AND user_id = {user_id};')
    result = cursor.fetchall()
    if len(result) == 0:
        return None
    else:
        created = result[0][0].replace(tzinfo=UTC)
        card = Carte(created=created)
        ratings = get_ratings_from_card_id(card_id, stringForm=False)
        for rating in ratings:
            card.rate(rating)
    
    return card.due()


def get_due_cards_from_deck_id(deck_id: int, user_id: int = Constants.temp_user_id, card_table = Constants.cards_table) -> list[int]:
    '''Retourne les dates (datetime(UTC)) de toutes les cartes associées à un deck et un utilisateur donné. 
    '''
    deckInfos, cards = get_deck_from_id(deck_id, user_id)
    idnDatetime = {}
    #quelque chose du style: {1: datetime(...), 2: datetime(...), ...}
    for card in cards:
        idnDatetime[card['card_id']] = card['created']

    cursor = db.query(f'SELECT created FROM {card_table} WHERE user_id = {user_id};')
    result = cursor.fetchall()
    if len(result) == 0:
        return list(idnDatetime.keys())
    else:
        present = datetime.now(UTC)
        reviews = get_reviews_from_deck_id(deck_id)
        '''Exemple de reviews:
        [
            (0, 0, 1, 'Good', datetime.datetime(2024, 5, 12, 18, 11, 42)),
            (1, 0, 1, 'Good', datetime.datetime(2024, 5, 12, 18, 11, 42)),
            ...
        ]
        '''
        dues = []
        idk = {}
        dico = {'Again': Rating.Again, 'Hard': Rating.Hard, 'Good': Rating.Good, 'Easy': Rating.Easy}

        for card_id, dt in idnDatetime.items():
            #ajoute une entrée dans le dico "idk" pour chaque carte du deck, genre {1: {'ratings': [],'created': datetime(..., tzinfo=datetime.timezone.utc)}, 2: {...} }
            idk[card_id] = {'ratings': [],'created': dt.replace(tzinfo=UTC)}
        
        for review in reviews:
            #remplis les listes 'ratings' dans les valeurs, par exemple {1: {'ratings': [Rating.Again, Rating.Good],'created': datetime(...,, tzinfo=datetime.timezone.utc)}, 2: {...} }
            #datetime correspondant à la création de la carte
            card_id = review[0]
            idk[card_id]['ratings'].append(dico[review[3]])

        for card_id, infos in idk.items():
            ratings = infos['ratings']
            card = Carte(created=infos['created'])
            for rating in ratings:
                card.rate(rating)
            if card.due() - present < timedelta(seconds=5):
                dues.append(card_id)
    return dues
