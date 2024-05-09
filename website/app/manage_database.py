import mysql.connector
from datetime import datetime


class DB:
    # en gros: se connecte à la base de données quand nécessaire, pas de pb d'actualisation comme ça
    conn = None

    def connect(self):
        self.conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='!nxbTjiPw7@Pb8',
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


class Constants:
    cards_table = 'cards2'
    decks_table = 'decks'
    temp_user_id = 1


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


def create_deck(user_id=Constants.temp_user_id, name='name', description='description', decks=Constants.decks_table) -> None:
    deck_id = get_free_id(decks)
    now = datetime.now()
    created = now.strftime("%Y-%m-%d %H:%M:%S")
    string = f'INSERT INTO {decks} VALUES ({deck_id},{user_id},"{name}","{description}","{created}");'
    db.query(string)

def delete_deck(deck_id, table=Constants.decks_table):
    db.query(f"DELETE FROM {table} WHERE deck_id = {deck_id};")

def create_card(deck_id=1, front="front", front_sub="front_sub", back="back", back_sub="back_sub", back_sub2="back_sub2", tag="tag", table=Constants.cards_table, user_id=Constants.temp_user_id) -> None:
    card_id = get_free_id()
    string = f'INSERT INTO {table} VALUES ({card_id},{user_id},"{deck_id}","{front}","{front_sub}","{back}","{back_sub}","{back_sub2}","{tag}");'
    db.query(string)


def delete_card(card_id, table=Constants.cards_table) -> None:
    db.query(f"DELETE FROM {table} WHERE card_id = {card_id};")


def delete_all_cards(table=Constants.cards_table) -> None:
    ids = get_all_ids(table)
    for card_id in ids:
        delete_card(card_id)

def delete_all_decks(table=Constants.decks_table):
    ids = get_all_ids(table)
    for deck_id in ids:
        delete_deck(deck_id)

def delete_everything(deck_table=Constants.decks_table, card_table=Constants.cards_table):
    delete_all_decks(deck_table)
    delete_all_cards(card_table)

def get_deck_list_from_user(user_id=Constants.temp_user_id, table=Constants.decks_table) -> list[tuple[int, str]]:
    cursor = db.query(f'SELECT * FROM {table} WHERE user_id = {user_id};')
    result = cursor.fetchall()
    liste = []
    for row in result:
        liste.append((row[0], row[2]))
    return liste


def get_decks_from_user(user_id=Constants.temp_user_id, table=Constants.decks_table, cards_table=Constants.cards_table) -> dict:
    cursor = db.query(f'SELECT * FROM {table} WHERE user_id = {user_id};')
    result = cursor.fetchall()
    decks = []
    for row in result:
        count = len(db.query(f'SELECT front FROM {cards_table} WHERE deck_id = {row[0]};').fetchall())
        decks.append({'deck_id': row[0], 'name': row[2], 'description': row[3], 'created': row[4], 'card_count': count})
    return decks


def get_deck_from_id(deck_id, user_id, decks_table=Constants.decks_table, cards_table=Constants.cards_table):
    #1ère requête pour vérifier si un deck existe pour un utilisateur donné
    cursor = db.query(f'SELECT * FROM {decks_table} WHERE {decks_table}.deck_id = {deck_id} AND {decks_table}.user_id = {user_id};')
    result = cursor.fetchall()
    if len(result) == 0:
        return None
    else:
        firstRow = result[0]
        #garde les infos du deck dans une variable
        deckInfos = {'deck_id': firstRow[0], 'name': firstRow[2], 'description': firstRow[3], 'created': firstRow[4]}
        #2ème requête pour obtenir toutes les cartes de ce deck, met les les cartes dans une liste cards
        cursor = db.query(f'SELECT * FROM {cards_table} WHERE {cards_table}.deck_id = {deck_id} AND {cards_table}.user_id = {user_id};')
        result = cursor.fetchall()
        cards = []
        for row in result:
            cards.append({'card_id': row[0], 'front': row[3], 'front_sub': row[4], 'back': row[5], 'back_sub': row[6], 'back_sub2': row[7], 'tag': row[8]})
        return (deckInfos, cards)
