from app.manage_database import DB, Constants, get_deck_from_id
from fsrs import *

db = DB()



def get_review_history_from_table(card_id, table=Constants.reviews_table) -> list[Rating] | None:
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

def get_due_cards_from_deck_id(deck_id, card_table=Constants.cards_table, deck_table=Constants.decks_table, reviews_table=Constants.reviews_table):
    deckInfos, cards = get_deck_from_id(deck_id)
    cursor = db.query(f'SELECT * FROM {reviews_table}')
    result = cursor.fetchall()

    cardIdsFromCards2 = []
    for i in range(len(cards)):
        cardIdsFromCards2.append(cards[i]['card_id'])
    print(cardIdsFromCards2)

    