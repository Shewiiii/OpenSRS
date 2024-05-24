from app.model import Carte
from app.constants import Constants
from app.reviews import dt, get_fsrs_from_reviews, reschedule_cards
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


jpdb_dict = {
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
    save_in_db: bool = True,
    from_db: bool = True,
    params: tuple = Constants.jpdb_updated_params,
    retention: tuple = Constants.default_retention,
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

            exists (bool): Si le deck existe déjà et qu'on souhaite
            le compléter.

            deck_id (id): L'identifiant du deck.

            save_in_db (bool): Sauvegarde les données scrapées de jpdb dans
            la table jpdb.

            from_db (bool): Récupère les infos de la table jpdb pour accélérer
            la génération de cartes.
            
            params (tuple): Les paramètres FSRS à utiliser.

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
            card = {}
            if from_db:
                # Requête vers la table jpdb:
                card = get_card_from_db(vid, word, deck_id)
                if card != {}:
                    print(f'Mot {card['word']} ajouté de la table')
                    wait = False

            if card == {} or not from_db:
                # Requête vers le site jpdb:
                # Récupère la lecture, définition, 
                # phrases et le pitch accent du mot
                card = get_card_from_jpdb(vid, word, deck_id)
                wait = True
    
            f_meaning = card['meanings'][0].replace('1. ', '')

            # Récupère les reviews du mot dans le json
            reviews = word_entry['reviews']

            # Récupère les variables FSRS en fonction des reviews
            variables = get_fsrs_from_reviews(
                card_id,
                user_id,
                reviews,
                add_review=True,
                deck_id=deck_id,
                rating_dict=jpdb_dict,
                rating_key='grade',
                params=params,
                retention=retention
            )

            # Intègre tout dans OpenSRS
            create_card(
                card_id=card_id,
                deck_id=deck_id,
                front=card['word'],
                front_sub=card['jp_sentence'],
                back=f"{card['reading']} - {f_meaning}",
                back_sub=card['en_sentence'],
                back_sub2=f'Pitch Accent: {card['pitchaccent']}',
                tag='jpdb',
            )
            update_card_srs_from_dict(card_id, variables, user_id)

            # Sauvgarde les données dans la table jpdb si voulu
            if save_in_db:
                add_jpdb_entry(
                    vid,
                    word,
                    card['reading'],
                    f_meaning,
                    card['jp_sentence'],
                    card['en_sentence'],
                    card['pitchaccent'],
                )
            # Attend entre chaque requête
            if wait:
                time.sleep(0.6)
