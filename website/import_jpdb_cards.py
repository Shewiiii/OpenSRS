import requests
from app.manage_database import *
from bs4 import BeautifulSoup
import time
import re


def request(url: str, cookie: dict | None = None) -> BeautifulSoup:
    '''Crée une instance BeautifulSoup à partir d'un url.

        Paramètres:
            url (str): Lien vers le site.
            cookie (dict): Cookies à charger (ex: {'sid': [UN STRING]}).
    '''
    print(f'request: {url}')
    if cookie:
        raw = requests.get(url, cookies=cookie)
    else:
        raw = requests.get(url)
    raw.encoding = 'UTF-8'
    return BeautifulSoup(raw.text, features='html.parser')


def get_pitchaccent_pattern_from_div(
    div: BeautifulSoup
) -> str:
    '''Retourne le pitch accent pattern sous forme d'un string.

        Paramètre:
            div (BeautifulSoup): La div contenant 
            le motif du pitch accent (jpdb).
    '''
    divs = div.find_all('div')
    moras = []
    kana = []
    pitchaccent_pattern = ''
    for div in divs:
        style = div['style']
        # div avec les divs
        if 'linear-gradient' in style:
            moras.append(div)

        # les divs avec les kana
        elif 'background-color' in style:
            kana.append(div.text)

    for mora in moras:
        if '--pitch-high-s' in str(mora):
            pitchaccent_pattern += 'H'
        elif '--pitch-low-s' in str(mora):
            pitchaccent_pattern += 'L'
        elif '--pitch-high-s' in str(mora):
            pitchaccent_pattern += 'H'

    final = ''
    # string de la longueur du mot
    for i in range(len(kana)):
        final += pitchaccent_pattern[i]*len(kana[i])

    return final


def import_deck(
    sid: str,
    jpdb_deck_id: int,
    cards_count: int,
    name: str = 'Deck jpdb importé',
    description: str = 'Ceci est un deck importé de jpdb.',
    user_id: str = Constants.temp_user_id,
    parameters: str = '&show_only=new&sort_by=by-frequency-global',
) -> list:
    '''Importe un deck présent sur jpdb vers OpenSRS.

        Paramètres:
            sid (str): Cookies du compte contenant les decks à importer.
            Note: Il est FORTEMENT recommandé d'utiliser les cookies d'un compte secondaire.

            jpdb_deck_id (id): L'id du deck, présent dans l'url du deck.

            cards_count (int): Nombre de cartes à importer.

            parameters (str):  Les paramètres de tri/filtrage de la page.
            Sont ajoutées après l'url du deck.

            name (str): Nom du deck sur OpenSRS.

            description (str): Description dur deck sur OpenSRS.

            user_id (int): L'id de l'utilisateur propriétaire du deck.

        Retourne:
            cards (dict): Une liste contenant un dictionnaire 
            pour chacune des cartes.
            Les clés sont: 'vid', 'word', 'meanings', 'reading',
            'jp_sentence', 'en_sentence', 'pitchaccent'.
    '''
    if name == 'Deck jpdb importé':
        name += f' {jpdb_deck_id}'

    cookie = {'sid': sid}
    url = f'https://jpdb.io/deck?id={jpdb_deck_id}' + parameters

    pages = cards_count//50 + 1
    added_words = 0
    jpdb_words = []

    # Premier passage: on retient les mots à ajouter plus tard:
    for i in range(pages):
        raw = request(f'{url}&offset={pages*50}', cookie)
        divs = raw.find_all('div', {'class': 'entry new'})

        for new_div in divs:
            if added_words < cards_count:
                a = BeautifulSoup(
                    str(new_div.find('div', {'class': 'vocabulary-spelling'})),
                    features='html.parser'
                ).find('a')

                word = a.text
                vid = re.findall(r'\d+', a['href'])[0]

                raw_a = str(a)
                reading = ''
                for letter in raw_a:
                    if 12354 <= ord(letter) <= 12538:
                        reading += letter

                meanings = new_div.find('div').find_all(
                    'div')[-1].text.split(';')
                for i in range(len(meanings)):
                    meanings[i] = meanings[i].strip()

                jpdb_words.append({
                    'vid': vid,
                    'word': word,
                    'meanings': meanings,
                    'reading': reading,
                })
            added_words += 1

        # Attendre entre chaque requête
        time.sleep(0.6)

    # Deuxième passage: on collecte les infos de chaque mot
    # à partir de la page vocabulary
    # (phrase, phrase traduite et pitch accent)
    cards = []
    for word in jpdb_words:
        url = f'https://jpdb.io/vocabulary/{word['vid']}/{word['word']}'

        raw = request(url, cookie)
        example = raw.find('div', {'class': 'subsection-examples'})

        jp_sentence = ''
        en_sentence = ''
        if example != None:
            jp = example.find('div', {'class': 'jp'})
            if jp:
                jp_sentence = jp.text

            en = example.find('div', {'class': 'en'})
            if en:
                en_sentence = en.text

        pitchaccent_div = raw.find(
            'div', {'style': 'word-break: keep-all; display: flex;'})
        if pitchaccent_div:
            pitchaccent = get_pitchaccent_pattern_from_div(pitchaccent_div)
        else:
            pitchaccent = ''

        card = word
        card.update({
            'jp_sentence': jp_sentence,
            'en_sentence': en_sentence,
            'pitchaccent': pitchaccent,
        })
        cards.append(card)
        # Attendre entre chaque requête
        time.sleep(0.6)

    # Dernière étape: créer le deck
    deck_id = get_free_id()
    create_deck(
        user_id=user_id,
        deck_id=deck_id,
        name=name,
        description=description,
    )

    for card in cards:
        f_meaning = card['meanings'][0].replace('1. ', '')
        create_card(
            deck_id=deck_id,
            front=card['word'],
            front_sub=card['jp_sentence'],
            back=f"{card['reading']} - {f_meaning}",
            back_sub=card['en_sentence'],
            back_sub2=f'Pitch Accent: {card['pitchaccent']}',
            tag='jpdb',

        )
    return cards


def get_card_from_jpdb(
    vid: int,
    word: str,
    deck_id: int,
) -> dict:
    '''Crée un dictionnaire card à partir de jpdb.

        Paramètre:
            vid (int): l'id d'un mot sur jpdb , trouvable dans l'url.
            word (str): une forme du mot associé à ce vid.
            deck_id (int): l'id du deck auquel la carte doit être associé.

        Retourne:
            card (dict): Contient les éléments suivants:

                'deck_id': L'id du deck mise en paramètre.

                'word': Le mot en japonais.

                'vid': L'id d'un mot sur jpdb , trouvable dans l'url.

                'reading': La lecture du mot en kana.

                'meanings': La/les définition(s) du mot.

                'jp_sentence': La première phrase d'exemple présente sur la page
                du mot sur jpdb, en japonais (si disponible).

                'en_sentence': La traduction de la phrase en Anglais (si disponible).

                'pitchaccent': Le pitch accent du mot.
                (ex: LHHH pour un mot Heiban à 4 mores)
    '''
    # Requête initiale
    url = f'https://jpdb.io/vocabulary/{vid}/{word}'
    raw = request(url)

    # Trouve la lecture du mot (mot en kana)
    raw_spelling = str(raw.find('div', {'class': 'primary-spelling'}))
    reading = ''
    for letter in raw_spelling:
        if 12354 <= ord(letter) <= 12538:
            reading += letter

    # Trouve les définitions du mot
    meanings = []
    raw_meanings = raw.find('div', {'class': 'subsection-meanings'})
    raw_meanings = raw_meanings.find_all('div', {'class': 'description'})
    for meaning in raw_meanings:
        meanings.append(meaning.text)

    # Trouve des phrases exemples du mot
    example = raw.find('div', {'class': 'subsection-examples'})

    jp_sentence = ''
    en_sentence = ''
    if example != None:

        jp = example.find('div', {'class': 'jp'})
        if jp:
            jp_sentence = jp.text

        en = example.find('div', {'class': 'en'})
        if en:
            en_sentence = en.text

    # Trouve le motif indiquant le pitch accent, et le traduit en string
    pitchaccent_div = raw.find(
        'div', {'style': 'word-break: keep-all; display: flex;'})

    if pitchaccent_div:
        pitchaccent = get_pitchaccent_pattern_from_div(pitchaccent_div)
    else:
        pitchaccent = ''

    # Crée le dictionnaire
    card = {
        'deck_id': deck_id,
        'word': word,
        'vid': vid,
        'reading': reading,
        'meanings': meanings,
        'jp_sentence': jp_sentence,
        'en_sentence': en_sentence,
        'pitchaccent': pitchaccent,
    }

    return card


def get_card_from_db(
    vid: int,
    word: str,
    deck_id: int,
    table: str = Constants.jpdb_table,
) -> dict:
    card = {}
    cursor = db.query(f"""SELECT * FROM {table} """
                      f"""WHERE vid = %s AND word = %s;""",
                      (vid, word))
    result = cursor.fetchall()
    for row in result:
        card = {
            'deck_id': deck_id,
            'word': row[1],
            'vid': row[0],
            'reading': row[2],
            'meanings': [row[3]],
            'jp_sentence': row[4],
            'en_sentence': row[5],
            'pitchaccent': row[6],
        }
    return card
