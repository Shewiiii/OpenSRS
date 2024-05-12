from app.manage_database import *
from datetime import datetime, timedelta, UTC
from app.model import Carte
from fsrs import *
db = DB()



def get_review_history_from_table(card_id: int, table=Constants.reviews_table) -> list[Rating] | None:
    reviews = []
    cursor = db.query(f'SELECT rating FROM {table} WHERE card_id = {card_id}')
    result = cursor.fetchall()
    if len(result) == 0:
        return None
    else:
        dico = {'Again': Rating.Again, 'Hard': Rating.Hard, 'Good': Rating.Good, 'Easy': Rating.Easy}
        for row in result:
            reviews.append(dico[row[0]])
        return reviews


def get_due_date_from_card_id(card_id: int, user_id: int = Constants.temp_user_id, card_table = Constants.cards_table) -> datetime:
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


#Note: je sais que la fonction suivante n'est pas vraiment optimisée, car 1 requête SQL est faite par carte, 
#mais sont néanmoins beaucoup plus facile à comprendre et à intégrer dans d'autres fonctions
 

def get_due_cards_from_deck_id(deck_id: int, user_id: int = Constants.temp_user_id, card_table = Constants.cards_table) -> list[int]:
    card_ids = get_card_ids_from_deck_id(deck_id)
    cursor = db.query(f'SELECT created FROM {card_table} WHERE user_id = {user_id};')
    result = cursor.fetchall()
    if len(result) == 0:
        return card_ids
    else:
        present = datetime.now(UTC)
        dues = []
        for card_id in card_ids:
            created = result[0][0].replace(tzinfo=UTC)
            card = Carte(created=created)
            ratings = get_ratings_from_card_id(card_id, stringForm=False)
            for rating in ratings:
                card.rate(rating)
            if card.due() - present < timedelta(minutes=1):
                dues.append(card_id)
    dues.sort()
    return dues

#Note2: version + compliqué, mais fais maintenant seulement 3 requêtes SQL, peu importe la taille du deck !

def get_due_cards_from_deck_id2(deck_id: int, user_id: int = Constants.temp_user_id, card_table = Constants.cards_table) -> list[int]:
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
