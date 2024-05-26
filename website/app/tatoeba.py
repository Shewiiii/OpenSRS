import requests
import json
from random import randint
from os import listdir
import pathlib
import pandas as pd

root = pathlib.Path(__file__).parents[1] / 'local_data'

pitch_path = root / 'pitch_accent'
pitch_files = listdir(pitch_path)
pitch_list = []
for file in pitch_files:
    file_path = pitch_path / file
    f = open(file_path, encoding='UTF-8')
    pitch_list += json.load(f)

tatoeba_path = root / 'tatoeba'
mono_data = pd.read_csv(tatoeba_path / 'jp_sentences.tsv', sep='\t',)
duo_data = pd.read_csv(tatoeba_path / 'jp_eng_sentences.tsv', sep='\t',)

mono_sentences = list(mono_data['jp_sentence'])
duo_sentences = {}
for i in range(len(duo_data)):
    duo_sentences[duo_data['jp_sentence'][i]] = duo_data['en_sentence'][i]


def is_kanji(word):
    for letter in word:
        if 12354 <= ord(letter) <= 12538:
            return False
    return True


def is_relevent(word: str, jp: str, en: str = '') -> bool:
    i = jp.find(word)
    jp_len = len(jp)
    en_len = len(en)
    if jp_len > 70 or en_len > 140:
        return False
    
    if is_kanji(word):
        if i != 0 and is_kanji(jp[i-1]):
            return False
        if i+len(word) <= jp_len-1:
            if is_kanji(jp[i+len(word)]):
                return False

    else:
        pre_particles = [
            'は',
            'が',
            'に',
            'の',
            'へ',
            'を',
            'と',
            'や',
            'と',
            'ど',
            'も',
            'ら',
            'り',
            'い',
            'で',
            'ど',
            'う',
            'か',
            'も',
            'い',
            '、',
            '。',
            '　',
            '？',
            '！',
        ]
        post_particles = [
            'だ',
            'で',
            'の',
            'は',
            'が',
            'が',
            'と',
            'い',
            'し',
            'ば',
            'よ',
            '、',
            '。',
            '　',
            '？',
            '！',
        ]
        if i != 0:
            if (not is_kanji(jp[i-1]) 
                and jp[i-1] not in pre_particles):
                return False
        if i+len(word) <= jp_len-1:
            if (not is_kanji(jp[i+len(word)]) 
                and jp[i+len(word)] not in post_particles):
                return False

    return True


def get_examples_v2(
    word: str,
    shortest: bool = True
) -> dict:
    '''Retourne une phrase d'exemple et sa traduction
        (si disponible).
        Se base sur des fichiers locaux dans le dossier tatoeba.
        
        1600 fois plus rapide que "get_exemples" si shortest == False,
        70 fois plus rapide si shortest == True.
        
        Vérifie si les phrases sont pertinantes (wip).
    '''
    examples = {
        'jp_sentence': '',
        'en_sentence': '',
    }
    jp_len = 999999
    # Recherche dans le dictionnaire de phrase jp_en
    for jp_sentence, en_sentence in duo_sentences.items():
        if word in jp_sentence:
            if is_relevent(word, jp_sentence, en_sentence):
                new_jp_len = len(word)
                if jp_len > new_jp_len:
                    examples['jp_sentence'] = jp_sentence
                    examples['en_sentence'] = en_sentence

                    if not shortest:
                        return examples
                    else:
                        jp_len = len(examples['jp_sentence'])

    # Recherche dans la liste de phrases japonaises
    # Si aucun résultat n'a été trouvé
    if examples['jp_sentence'] == '':
        for jp_sentence in mono_sentences:
            if word in jp_sentence:
                if is_relevent(word, jp_sentence):

                    new_jp_len = len(word)
                    if jp_len > new_jp_len:
                        examples['jp_sentence'] = jp_sentence

                        if not shortest:
                            return examples
                        else:
                            jp_len = len(examples['jp_sentence'])

    return examples


def get_examples(
    word: str,
    random: bool = True,
    mono_params: str = '&to=',
    multi_params: str = '&to=eng',
) -> dict:
    '''Retourne une phrase d'exemple et sa traduction
       (si disponible).
    '''
    examples = {
        'jp_sentence': '',
        'en_sentence': '',
    }

    url = ('https://tatoeba.org/en/api_v0/search?from=jpn&query='
           f'"{word}"&word_count_max=50')
    raw = requests.get(url + multi_params)
    print('request:', url)
    results = raw.json()['results']

    if results != []:

        sentences = len(results)
        if random:
            sentence = results[randint(0, sentences-1)]
        else:
            sentence = results[0]
        examples['jp_sentence'] = sentence['text']
        for t in sentence['translations'][0]:
            if t['lang'] == 'eng':
                examples['en_sentence'] = t['text']

    else:
        raw = requests.get(url + mono_params)
        results = raw.json()['results']

        if results != []:
            sentences = len(results)
            if random:
                sentence = results[randint(0, sentences-1)]
            else:
                sentence = results[0]
            examples['jp_sentence'] = sentence['text']

    return examples


def get_pitchaccent(word: str, and_reading: bool = False) -> str:
    '''Retourne le pitch accent d'un mot sous la forme d'un string.
    '''
    str_pitch = ''
    reading = ''
    for pitch in pitch_list:
        if word in pitch:
            int_pitch = pitch[2]['pitches'][0]['position']
            reading = pitch[2]['reading']
            word_len = len(reading)

            if int_pitch == 0:
                str_pitch += 'L' + 'H'*(word_len-1)

            elif int_pitch == 1:
                str_pitch = 'H' + 'L'*(word_len-1)

            else:
                str_pitch = 'L' + 'H'*(int_pitch-1) + 'L'*(word_len-int_pitch)
                if int_pitch == word_len:
                    str_pitch += '(L)'

            if and_reading:
                return str_pitch, reading
            else:
                return str_pitch
    
    if and_reading:
        return '',''
    else:
        return ''


def get_word_infos(word: str) -> dict:
    '''Retourne le pitch accent d'un mot sous la forme d'un string.
    '''
    # Pitch accent et reading
    pitchaccent = get_pitchaccent(word)

    # Phrases exemple
    sentences = get_examples_v2(word)
    jp_sentence = sentences['jp_sentence']
    en_sentence = sentences['en_sentence']

    return {
        'word': word,
        'jp_sentence': jp_sentence,
        'en_sentence': en_sentence,
        'pitchaccent': pitchaccent,
    }
