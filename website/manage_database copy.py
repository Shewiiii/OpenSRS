import mysql.connector
from datetime import datetime, timezone
from app.secret import Trucs
from app.constants import Constants
import re
from fsrs import Rating
from app.model import Carte


class DB:
    # en gros: se connecte à la base de données quand nécessaire, pas de pb d'actualisation comme ça
    conn = None

    def connect(self):
        self.conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password=Trucs.mdp,
            database='cards')

    def query(self, sql):
        print(sql)
        try:
            cursor = self.conn.cursor(buffered=True)
        except:
            self.connect()
            cursor = self.conn.cursor(buffered=True)
        cursor.execute(sql)
        self.conn.commit()
        return cursor


db = DB()


class Card:
    def __init__(self, id) -> None:
        self.id = id
        # ...


def get_all_ids(table=Constants.cards_table) -> list:
    ids = []
    cursor = db.query(f"SELECT * FROM {table}")
    result = cursor.fetchall()
    for row in result:
        ids.append(row[0])
    return ids


def get_free_id(table=Constants.cards_table) -> int:
    cursor = db.query(f'SELECT * FROM {table};')
    result = cursor.fetchall()
    if len(result) == 0:
        return 0
    else:
        lastid = result[-1][0]
        print("lastid:", lastid)
        return lastid+1


def remove_ghost_reviews(
        card_table=Constants.cards_table,
        reviews_table=Constants.reviews_table
) -> None:
    '''Ne devrait être utilisé que en cas d'erreurs.
    '''
    ids = get_all_ids(card_table)
    cursor = db.query(f'SELECT card_id FROM {reviews_table};')
    result = cursor.fetchall()
    for row in result:
        card_id = row[0]
        if card_id not in ids:
            db.query(
                f'DELETE FROM {reviews_table} WHERE card_id = {card_id};'
            )


def add_image(
        deck_id: int,
        extension: str,
        table=Constants.image_table
) -> int:
    '''Associe une image sous format .jpg, .png ou .gif à un deck donné.

        Retourne l'id de l'image dans la table images.
    '''
    cursor = db.query(f'SELECT img_id FROM {table} WHERE deck_id = {deck_id}')
    result = cursor.fetchall()

    if len(result) != 0:
        print(f"image déjà existante à l'ID {result[0][0]}, remplacage..")
        db.query(f'UPDATE {table}\
                 SET extension = "{extension}" WHERE deck_id = {deck_id};')
        return result[0][0]

    else:
        img_ig = get_free_id(table=table)
        db.query(f'INSERT INTO {table}\
                  VALUES ({img_ig},{deck_id},"{extension}");')

        return img_ig


def delete_image(deck_id: int) -> None:
    '''Supprime dans la table images l'entrée d'une image d'un deck donné. 
    '''
    db.query(f'DELETE FROM images WHERE deck_id = {deck_id};')


def get_img(
        deck_id: int,
        table=Constants.image_table
) -> tuple[int, str]:
    '''Retourne un tuple contenant l'id de l'image dans la table image, et son extension.
    '''
    cursor = db.query(f'SELECT img_id, extension\
                      FROM {table} WHERE deck_id = {deck_id};')
    result = cursor.fetchall()

    if len(result) == 0:
        return (None, None)

    else:
        return (result[0][0], result[0][1])


def create_deck(
        user_id: str = Constants.temp_user_id,
        name: str = 'name',
        description: str = 'description',
        decks_table: str = Constants.decks_table,
) -> None:
    '''Crée un deck associé à un utilisateur en ajoutant une entrée dans la table decks.
    '''
    deck_id = get_free_id(decks_table)
    now = datetime.now()
    created = now.strftime("%Y-%m-%d %H:%M:%S")
    db.query(f'INSERT INTO {decks_table}\
            VALUES ({deck_id},{user_id},"{name}",\
            "{description}","{created}");')


def delete_deck(
        deck_id: int,
        deck_table: str = Constants.decks_table,
        card_table: str = Constants.cards_table,
        reviews_table: str = Constants.reviews_table,
) -> None:
    '''Supprime un deck, son image et toutes ses cartes associées les tables correspondantes.
    '''
    db.query(f"DELETE FROM {deck_table},{card_table},{reviews_table}\
             WHERE deck_id = {deck_id};")
    delete_image(deck_id)


def create_card(
        deck_id = 1,
        card_id = None,
        front: str = "front",
        front_sub: str = "front_sub",
        back: str = "back",
        back_sub: str = "back_sub",
        back_sub2: str = "back_sub2",
        tag: str = "tag",
        cards_table: str = Constants.cards_table,
        srs_table: str = Constants.srs_table,
        user_id: str = Constants.temp_user_id,
) -> None:
    '''Crée une carte associé à un deck et un utilisateur en ajoutant une entrée dans la table cards2.
    '''
    if card_id == None:
        card_id = get_free_id()
    now = datetime.now()
    created = now.strftime("%Y-%m-%d %H:%M:%S")
    db.query(f'INSERT INTO {cards_table}\
            VALUES ({card_id},{user_id},"{deck_id}",\
            "{front}","{front_sub}","{back}","{back_sub}",\
            "{back_sub2}","{tag}","{created}");')

    card = Carte()
    p = card.getParameters()
    string = f'INSERT INTO {srs_table}\
             VALUES ({card_id}, {deck_id}, {user_id}, "{p['due']}",\
             {p['stability']},{p['difficulty']}, {p['scheduled_days']},\
             {p['reps']}, {p['lapses']}, "{p['state']}",'

    if p['last_review'] == None:
        string += "NULL);"

    else:
        string += f'''"{p['last_review']}");'''

    db.query(string)


def delete_card(
        card_id: int,
        card_table: str = Constants.cards_table,
        review_table: str = Constants.reviews_table,
        srs_table: str = Constants.srs_table,
) -> None:
    '''Supprime toutes les cartes d'un deck donné.
    '''
    db.query(f"DELETE FROM {card_table} WHERE card_id = {card_id};")
    db.query(f"DELETE FROM {review_table} WHERE card_id = {card_id};")
    db.query(f"DELETE FROM {srs_table} WHERE card_id = {card_id};")


def delete_all_cards(table: str = Constants.cards_table,) -> None:
    '''Supprime toutes les cartes de tous les decks.
    '''
    ids = get_all_ids(table)
    for card_id in ids:
        delete_card(card_id)


def delete_everything(table: str = Constants.decks_table) -> None:
    '''Supprime TOUS les decks, leur images et toutes leur cartes associées les tables correspondantes.
    '''
    ids = get_all_ids(table)
    for deck_id in ids:
        delete_deck(deck_id)


def get_card_from_card_id(
        card_id: int,
        table=Constants.cards_table
) -> None | dict:
    '''Retourne les informations d'une carte sous forme d'un dictionnaire 
        à partir de son id.
    '''
    cursor = db.query(f'SELECT * FROM {table} WHERE card_id = {card_id}')
    result = cursor.fetchall()
    if len(result) == 0:
        return None
    else:
        row = result[0]
        dico = {
            'card_id': row[0],
            'deck_id': row[2],
            'front': row[3],
            'front_sub': row[4],
            'back': row[5],
            'back_sub': row[6],
            'back_sub2': row[7],
            'tag': row[8],
            'created': row[9]
        }

        return dico


def get_cards_from_list(
    card_ids: list,
    deck_id: int,
    table=Constants.cards_table
) -> None | dict:
    '''Retourne les informations d'une carte sous forme d'un dictionnaire 
        à partir d'une liste d'ids.
    '''
    string = f"SELECT * FROM {table} WHERE deck_id = {deck_id} AND"
    for card_id in card_ids:
        string += f'card_id = {card_id} OR '

    string = string[:-3] + ';'
    cursor = db.query(string)
    result = cursor.fetchall()

    if len(result) == 0:
        return None

    else:
        cards = []
        for row in result:
            dico = {
                'card_id': row[0],
                'deck_id': row[2],
                'front': row[3],
                'front_sub': row[4],
                'back': row[5],
                'back_sub': row[6],
                'back_sub2': row[7],
                'tag': row[8],
                'created': row[9]
            }
            cards.append(dico)

        return cards


def get_deck_list_from_user(
        user_id=Constants.temp_user_id,
        table=Constants.decks_table,
) -> list[tuple[int, str]]:
    '''(Obsolète et spécifique) Retourne tous les decks associé à un utilisateur, 
        à partir de son id, sous forme d'une liste contenant
        des tuples d'ids et de noms de decks.
    '''
    cursor = db.query(f'SELECT * FROM {table} WHERE user_id = {user_id};')
    result = cursor.fetchall()
    liste = []

    for row in result:
        liste.append((row[0], row[2]))

    return liste


def get_decks_from_user(
        user_id=Constants.temp_user_id,
        table=Constants.decks_table,
        cards_table=Constants.cards_table,
) -> dict:
    '''Retourne tous les decks associé à un utilisateur, à partir de son id, sous forme d'un dictionnaire.
    '''
    cursor = db.query(f'SELECT * FROM {table} WHERE user_id = {user_id};')
    result = cursor.fetchall()
    decks = []
    for row in result:
        img_id, extension = get_img(row[0])
        count = len(db.query(f'SELECT front FROM {cards_table}\
                             WHERE deck_id = {row[0]};').fetchall())
        decks.append({
            'deck_id': row[0],
            'name': row[2],
            'description': row[3],
            'created': row[4],
            'card_count': count,
            'img_id': img_id,
            'extension': extension
        })

    return decks


def get_deck_from_id(
        deck_id: int,
        user_id: int,
        decks_table=Constants.decks_table,
        cards_table=Constants.cards_table,
) -> None | tuple[dict, list[dict]]:
    '''Retourne à partir de son id les informations d'un deck, ainsi que toutes les cartes contenues dans ce dernier.
    '''
    # 1ère requête pour vérifier si un deck existe pour un utilisateur donné
    cursor = db.query(f'SELECT * FROM {decks_table}\
                      WHERE {decks_table}.deck_id = {deck_id}\
                      AND {decks_table}.user_id = {user_id};')
    result = cursor.fetchall()

    if len(result) == 0:
        return None

    else:
        firstRow = result[0]
        # garde les infos du deck dans une variable
        deckInfos = {
            'deck_id': firstRow[0],
            'name': firstRow[2],
            'description': firstRow[3],
            'created': firstRow[4]
        }
        # 2ème requête pour obtenir toutes les cartes de ce deck, met les les cartes dans une liste cards
        cursor = db.query(f'SELECT * FROM {cards_table} \
                          WHERE {cards_table}.deck_id = {deck_id} \
                          AND {cards_table}.user_id = {user_id};')
        result = cursor.fetchall()
        cards = []

        for row in result:
            cards.append({
                'card_id': row[0],
                'front': row[3],
                'front_sub': row[4],
                'back': row[5],
                'back_sub': row[6],
                'back_sub2': row[7],
                'tag': row[8],
                'created': row[9]
            })

        return (deckInfos, cards)


def get_card_ids_from_deck_id(
        deck_id: int,
        user_id: int = Constants.temp_user_id,
) -> list[int]:
    '''Retourne tous les identifiants des cartes associées à un deck.
    '''
    deckInfos, cards = get_deck_from_id(deck_id, user_id)
    card_ids = []
    for card in cards:
        card_ids.append(card['card_id'])
    return card_ids


def add_review_entry(
        card_id: int,
        deck_id: int,
        user_id: int,
        rating: str,
        date: datetime | None = None,
        table=Constants.reviews_table,
) -> None:
    '''Ajoute une review dans la table reviews pour une carte, avec son deck et son utilisateur donné.
    '''
    # les ratings pouvant être: 'Again', 'Hard', 'Good', 'Easy'
    if date == None:
        date = datetime.now(timezone.utc)
    db.query(f'INSERT INTO {table} VALUES \
             ({card_id}, {deck_id}, {user_id}, "{rating}", "{date}");')


def update_card_srs(
        card_id: int,
        due: datetime,
        stability: float,
        difficulty: float,
        scheduled_days: int,
        reps: int,
        lapses: int,
        state: str,
        last_review: datetime,
        srs_table: str = Constants.srs_table,
) -> None:
    '''Met à jour l'état de la carte dans la table srs.
    '''
    db.query(
        f'UPDATE srs SET card_id = {card_id}, due = "{due}",\
        stability = {stability},\
        difficulty = {difficulty},\
        scheduled_days = {scheduled_days},\
        reps = {reps},\
        lapses = {lapses},\
        state = "{state}",\
        last_review = "{last_review}"'
    )


def update_card_srs(
        card_id: int,
        due: datetime,
        stability: float,
        difficulty: float,
        scheduled_days: int,
        reps: int,
        lapses: int,
        state: str,
        last_review: datetime,
) -> None:
    db.query(
        f'INSERT INTO srs VALUES \
        ({card_id},"{due}",{stability},{difficulty},\
        {scheduled_days},{reps},{lapses},"{state}",\
        "{last_review}"'
    )


def forget_card(
        card_id: int,
        table=Constants.reviews_table,
) -> None:
    '''Supprime toutes les reviews dans la table reviews d'une carte donnée.
    '''
    db.query(f"DELETE FROM {table} WHERE card_id = {card_id};")


def get_ratings_from_card_id(
        card_id: int,
        table=Constants.reviews_table,
        stringForm: bool = False,
) -> list:
    '''Retourne les Rating d'une carte donnée, sous forme de strings ou non. 
    '''
    cursor = db.query(f"SELECT * FROM {table} WHERE card_id = {card_id};")
    result = cursor.fetchall()
    ratings = []
    if stringForm == True:
        for row in result:
            ratings.append(row[2])
    else:
        for row in result:
            dico = {
                'Again': Rating.Again,
                'Hard': Rating.Hard,
                'Good': Rating.Good,
                'Easy': Rating.Easy,
            }
            ratings.append(dico[row[3]])

    return ratings


def get_reviews_from_deck_id(
        deck_id: int,
        table=Constants.reviews_table,
) -> dict:
    '''Retourne les reviews des cartes d'un deck donnée.
    '''
    # l'utilisation d'un dico rend la fonction bien plus intuitive à utiliser et la rend future proof
    cursor = db.query(f"SELECT * FROM {table} WHERE deck_id = {deck_id};")
    result = cursor.fetchall()
    reviews = []
    for row in result:
        reviews.append({
            'card_id': row[0],
            'deck_id': row[1],
            'user_id': row[2],
            'rating': row[3],
            'date': row[4]
        })

    return reviews


def get_reviews_from_list(
        card_ids: list,
        deck_id: int,
        table=Constants.reviews_table,
) -> dict:
    '''Retourne les reviews des cartes données dans une liste.
    '''
    string = f"SELECT * FROM {table} WHERE deck_id = {deck_id} AND "
    for card_id in card_ids:
        string += f'card_id = {card_id} OR '
    string = string[:-3] + ';'

    cursor = db.query(string)
    reviews = []
    result = cursor.fetchall()

    for row in result:
        reviews.append({
            'card_id': row[0],
            'deck_id': row[1],
            'user_id': row[2],
            'rating': row[3],
            'date': row[4]
        })

    return reviews


def test_login(
    username: str,
    password: str,
) -> str:
    '''Teste des identifiants de connection, renvoie l'user_id sous forme de string si ces derniers sont valides. 
    '''
    cursor = db.query(
        f'SELECT * FROM users WHERE username = "{username}" AND password = "{password}";')
    result = cursor.fetchall()

    if len(result) == 0:
        return None
    else:
        return str(result[0][0])
