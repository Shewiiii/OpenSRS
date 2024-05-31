from app.constants import Constants
from app.reviews import dt, get_fsrs_from_reviews, reschedule_cards
import json
import pathlib
from fsrs import Rating
from import_jpdb_cards import *
from app.tatoeba import *


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
    sid: str,
    deck_name: str = 'Deck importé de jpdb',
    deck_description: str = '',
    user_id: int = Constants.temp_user_id,
    directory_path=pathlib.Path(__file__).parents[0] / 'local_data' / 'jpdb',
    exists: bool = False,
    deck_id: int | None = None,
    card_count: int | str = 'all',
    from_db: bool = True,
    from_tatoeba: bool = True,
    params: tuple = Constants.jpdb_updated_params,
    retention: tuple = Constants.default_retention,
) -> None:
    '''Importe les données du json reviews de jpdb vers OpenSRS.

        Paramètres:
            json_filename (str): Le nom du json contenant tout
            l'historique d'un utilisateur de jpdb 
            (téléchargable dans les options).

            sid (str): Un cookie de connection jpdb.

            deck_name (str): Le nom du deck à créer sur OpenSRS.

            deck_description (str): Sa description.

            user_id (int): l'id de l'utilisateur propriétaire du deck.

            directory_path (pathlib ou string): chemin vers le 
            dossier contenant le fichier json. 

            exists (bool): Si le deck existe déjà et qu'on souhaite
            le compléter.

            deck_id (id): L'identifiant du deck.
            
            card_count (str,int): Le nombre de cartes à ajouter.

            from_db (bool): Récupère les infos de la table jpdb pour accélérer
            la génération de cartes.

            from_tatoeba (bool): Récupère les phrases d'exemple de tatoeba
            et le pitch accent de fichiers locaux. (Lent mais + précis)

            params (tuple): Les paramètres FSRS à utiliser.

            retention (tuple): La rétention souhaitée.

        Benchmark, importation de 15-05-24 review history.json,
        sans data dans la table jpdb:
            ver.0: ~2h+ ~100000 requêtes SQL
            (sans API tatoeba, juste jpdb)

            ver.1: ~2h+ ~100000 requêtes SQL
            (avec API tatoeba, un peu plus long que ver.0 mais + d'exemples)

            ver.2: 1h20 ~100000 requêtes SQL
            (avec API tatoeba + Pitch accent local)

            ver.3: 8min30  ~100000 requêtes SQL
            (avec Local tatoeba + Pitch accent local)

            ver.4: 6min ? ~95000 requêtes SQL
            (avec Local tatoeba + Pitch accent local + bulk create&srs)

            ver.5: 6min3 ~90000 requêtes SQL
            (avec Local tatoeba + Pitch accent local + bulk create&srs&jpdb)

            ver.6: ? ~6296 requêtes SQL
            (avec Local tatoeba + Pitch accent local 
            + bulk create&srs&jpdb&reviews)
            
            ver.7: 3min30 ~14 requêtes SQL
            (avec Local tatoeba + Pitch accent local 
            + bulk create&srs&jpdb&reviews&jpdb check)

    >>> jpdb_import(
        json_filename='15-05-24 review history.json',
        sid = '...',
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
        _, cards = get_deck_from_id(deck_id)
        for card in cards:
            processed_words.append(card['front'])

    # Définit les mots à ajouter (uniq. ceux étudiés)
    studied = import_deck(
        sid=sid,
        jpdb_deck_id='global',
        cards_count=card_count,
        parameters='&show_only=known,learning',
        create=False,
        deep_import=False,
        from_db=False,
    )
    # Instance la liste de cartes, variables, entrées jpdb et
    # toutes les reviews
    # pour les mettre dans les tables de façon groupée (++rapide)
    cards = []
    cards_variables = {}
    entries = []
    reviews = []

    # Instance la liste de review
    word_count = len(review_history)
    f_id = get_free_id(table=Constants.cards_table)
    card_ids = [i for i in range(f_id, f_id+word_count)]
    j = 0
    # Requête vers la table jpdb:
    db_cards = get_cards_from_db(deck_id)
    
    # Parcourt le json
    for i in range(word_count):

        # Récupère le vid et le mot
        word = review_history[i]['spelling']
        vid = review_history[i]['vid']

        # Vérifie si le mot est pas déjà dans le deck (si existe)
        if exists and word in processed_words:
            print(f'Mot déjà présent sauté: {word}')

        # Vérifie si fait partie des mots étudiés
        elif word not in studied:
            print(f'Mot pas étudié: {word}')

        else:
            small_card = studied[word]
            card = {}

            if from_db:
                if vid in db_cards:
                    card = db_cards[vid]
                    print(f"Mot {card['word']} ajouté de la table")
                    wait = False

            # Si pas trouvé dans la table et card de tatoeba
            if card == {} and from_tatoeba:
                card = {}
                card['reading'] = small_card['reading']
                card['vid'] = small_card['vid']
                card['meanings'] = [small_card['meaning']]

                tatoeba = get_word_infos(word)
                card.update(tatoeba)
                wait = False

            # Si pas trouvé dans la table et card de jpdb (lent)
            elif card == {} or not from_db:
                # Requête vers le site jpdb:
                # Récupère la lecture, définition,
                # phrases et le pitch accent du mot
                card = get_card_from_jpdb(vid, word, deck_id)
                wait = True

            f_meaning = card['meanings'][0].replace('1. ', '')

            # Récupère les reviews du mot dans le json
            jpdb_reviews = review_history[i]['reviews']

            # Récupère les variables FSRS en fonction des reviews (après)
            variables, card_reviews = get_fsrs_from_reviews(
                card_ids[j],
                user_id,
                jpdb_reviews,
                get_reviews=True,
                deck_id=deck_id,
                rating_dict=jpdb_dict,
                rating_key='grade',
                params=params,
                retention=retention
            )
            # Ajoute les reviews de la carte à la liste complète
            reviews += card_reviews
            # Intègre tout dans OpenSRS (après)
            open_card = {
                'card_id': card_ids[j],
                'deck_id': deck_id,
                'front': card['word'],
                'front_sub': card['jp_sentence'],
                'back': f"{card['reading']} - {f_meaning}",
                'back_sub': card['en_sentence'],
                'back_sub2': f"Pitch Accent: {card['pitchaccent']}",
                'tag': 'jpdb',
            }
            cards.append(open_card)
            print('Ajout:', word)
            cards_variables[card_ids[j]] = variables

            # Sauvgarde les données dans la table jpdb (après)
            jpdb_entry = {
                'vid': vid,
                'word': word,
                'reading': card['reading'],
                'meaning': f_meaning,
                'jp_sentence': card['jp_sentence'],
                'en_sentence': card['en_sentence'],
                'pitchaccent': card['pitchaccent'],
            }
            entries.append(jpdb_entry)

            # Attend entre chaque requête
            if wait:
                time.sleep(0.6)
                
            # j incrémente, correspond à l'indice de l'id de la carte.
            j += 1

    # Intègre tout en bulk:
    create_cards(deck_id, cards, user_id)
    add_review_entries(reviews)
    bulk_update_cards_srs(cards_variables)
    add_jpdb_entries(entries)

# delete_jpdb_data()
# ids = get_all_ids(table=Constants.decks_table)
# for id in ids:
#     delete_deck(id)
