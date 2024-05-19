from app.model import Carte
from app.constants import Constants
import json
import pathlib
from datetime import datetime, timezone
from fsrs import Rating
from import_jpdb_cards import *


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
    'fail': Rating.Again,
    'nothing': Rating.Again,
    'something': Rating.Again,
    'hard': Rating.Hard,
    'okay': Rating.Good,
    'easy': Rating.Easy,
}


def jpdb_import(
    json_filename: str,
    deck_name: str = 'Deck importé de jpdb',
    deck_description: str = '',
    user_id: int = Constants.temp_user_id,
    directory_path=pathlib.Path(__file__).parents[0] / 'jpdb',
    exists: bool = False,
    deck_id: int | None = None,

) -> None:
    '''Importe les données du json reviews de jpdb vers OpenSRS.

        Paramètres:
            json_filename (str): Le nom du json contenant tout
            l'historique d'un utilisateur de jpdb 
            (téléchargable dans les options).

            deck_name (str): Le nom du deck à créer sur OpenSRS.

            deck_description (str): Sa description.

            user_id (int): l'id de l'utilisateur propriétaire du deck.

            directory_path (pathlib ou string): chemin vers le 
            dossier contenant le fichier json. 

    >>> jpdb_import(
        json_filename='15-05-24 review history.json',
        deck_name='jpdb',
        deck_description=(
            '19/05/2024, deck importé de jpdb. '
            'Contient les mots déjà étudiés'))
    '''
    try:
        path = directory_path / json_filename
    except:
        try:
            path = f'{directory_path}/{json_filename}'
        except:
            raise ValueError('Wrong path format,'
                             'it should be a string or a pahlib')

    # Chargement du fichier
    file = open(path, encoding='UTF-8')
    jpdb_json = json.load(file)
    review_history = jpdb_json['cards_vocabulary_jp_en']

    # Création du deck
    processed_words = []
    if not exists:
        deck_id = get_free_id(table=Constants.decks_table)
        create_deck(
            user_id=user_id,
            deck_id=deck_id,
            name=deck_name,
            description=deck_description,
        )
    else:
        # Si deck déjà existant, fais la liste de tous les mots déjà présents
        _, cards = get_deck_from_id(deck_id, user_id)
        for card in cards:
            processed_words.append(card['front'])

    # Parcourt le json
    for word_entry in review_history:

        card_id = get_free_id(table=Constants.cards_table)

        # Récupère le vid et le mot
        word = word_entry['spelling']
        vid = word_entry['vid']

        # Vérifie si le mot est pas déjà dans le deck (si existe)
        if exists and word in processed_words:
            print(f'Mot déjà présent sauté: {word}')
        else:
            # Requête vers jpdb:
            # Récupère la lecture, définition, phrases et le pitch accent du mot
            card = get_card_from_jpdb(vid, word, deck_id)

            # Récupère les reviews du mot dans le json
            reviews = word_entry['reviews']

            # Récupère les variables FSRS en fonction des reviews
            first_review = dt(reviews[0]['timestamp'])
            card_srs = Carte(created=first_review)

            for review in reviews:
                timestamp = review['timestamp']
                date = dt(timestamp)
                try:
                    rating = rating_dict[review['grade']]
                    card_srs.rate(rating, now=date)
                    add_review_entry(card_id, deck_id, user_id, rating)
                except Exception as e:
                    print('Error', e)
            variables = card_srs.get_variables()

            # Intègre tout dans OpenSRS
            create_card(
                card_id=card_id,
                deck_id=deck_id,
                front=card['word'],
                front_sub=card['jp_sentence'],
                back=f"{card['reading']} - {card['meanings'][0]}",
                back_sub=card['en_sentence'],
                back_sub2=f'Pitch Accent: {card['pitchaccent']}',
                tag='jpdb',
            )
            update_card_srs_from_dict(card_id, variables, user_id)

            # Attend entre chaque requête
            time.sleep(0.6)
