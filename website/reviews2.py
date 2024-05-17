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
    cursor = db.query(f'SELECT due FROM {srs_table}\
                      WHERE card_id = {card_id}\
                      AND user_id = {user_id};')
    result = cursor.fetchall()

    if len(result) == 0:
        return None

    else:
        return result[0][0].replace(tzinfo=timezone.utc)



#POUR TESTS:
# from random import randint
# ids = get_all_ids()
# for id in ids:
#     for i in range(50):
#         add_review_entry(id, 0, 1, ['Again', 'Hard', 'Good', 'Easy'][randint(0,3)])

# ids = get_all_ids()
# for id in ids:
#     forget_card(id)
#for i in range(30):
#    create_card(deck_id=0)