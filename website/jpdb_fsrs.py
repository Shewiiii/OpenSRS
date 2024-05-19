from app.model import Carte
import json
import pathlib
from datetime import datetime, timezone
from fsrs import Rating


'''Review history sample:
{
    "cards_vocabulary_jp_en": [
        {
            "vid": 1605330,
            "spelling": "漏れる",
            "reading": "もれる",
            "reviews": [
                {
                    "timestamp": 1651250686,
                    "grade": "nothing",
                    "from_anki": true
                },
                {
                    "timestamp": 1651250772,
                    "grade": "nothing",
                    "from_anki": true
                },
                {
                    "timestamp": 1651250875,
                    "grade": "nothing",
                    "from_anki": true
                }
            ]
        }
    ]
}

'''


def dt(timestamp: int) -> datetime:
    '''Convertit un timestamp en datetime utc.
    '''
    date = datetime.fromtimestamp(timestamp)
    date = date.replace(tzinfo=timezone.utc)

    return date


rating_dict = {
    'nothing': Rating.Again,
    'something': Rating.Again,
    'hard': Rating.Hard,
    'okay': Rating.Good,
    'easy': Rating.Easy,
}

filename = 'Untitled-1.json'
path = pathlib.Path(__file__).parents[0] / 'jpdb' / filename
file = open(path, encoding='UTF-8')
jpdb_json = json.load(file)

review_history = jpdb_json['cards_vocabulary_jp_en']

for word in review_history:
    reviews = word['reviews']

    first_review = dt(reviews[0]['timestamp'])
    card = Carte(created=first_review)

    for review in reviews[1:]:
        timestamp = review['timestamp']
        date = dt(timestamp)

        rating = rating_dict[review['grade']]
        card.rate(rating, now=date)
        
    print(card.get_variables())
