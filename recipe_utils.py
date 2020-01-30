import os
from datetime import datetime
from dateutil.parser import parse

import Levenshtein
from nltk.tokenize import word_tokenize
from lxml import etree as et
from bs4 import BeautifulSoup as bs

def get_recipe_title(recipe:str)->str:
    soup = bs(recipe, features='lxml')
    
    title = soup.find('title').text
    return title

def get_content_tokens(recipe:str, skipPunctuation=True):
    punctuation = [',', '/', '.', '//', ')', '(']
    soup = bs(recipe, features='lxml')
    content = soup.find('content:encoded').text

    tokens = word_tokenize(content)

    if skipPunctuation:
        tokens = filter(lambda x: not x in punctuation, tokens)

    return list(tokens)

def exact_match(str1, str2):
    return str1 == str2

def fuzzy_match(str1, str2):
    # the maximum distance is based on the length 
    # of the first string
    dst = Levenshtein.distance(str1.lower().replace('*',''), str2.lower().replace('*',''))

    return dst < max(1, len(str1)/3)

def get_recipe(recipe):
    soup = bs(recipe, features='lxml')
    content = soup.find('content:encoded').text

    return content

def annotate_recipe(recipe, ingredients, matching=exact_match):
    recipe_tokens = get_content_tokens(recipe, skipPunctuation=False)

    for idx, token in enumerate(recipe_tokens):
        for ingredient in ingredients:
            if matching(token, ingredient):
                recipe_tokens[idx] = f'<objectName type="ingredient" ref="#{ingredient}">{token}</objectName>'
                break

    return ' '.join(recipe_tokens)

def get_ingredients(recipe):
    try:
        container = et.fromstring('<div>'+recipe+'</div>')
    except Exception:
        print(recipe)
    namespaces = {'xmlns': "http://www.tei-c.org/ns/1.0"}
    ingredients = container.xpath('.//objectName[@type="ingredient"]', namespaces=namespaces)
    s = set(c.get('ref') for c in ingredients)
    
    ref_2_tag = lambda x:f'\t\t<object type="ingredient" xml:id="{x[1:]}">{x[1:].capitalize()}</object>'
    ingredients_entities = '\n' + '\n'.join(map(ref_2_tag, s)) + '\n'
    return ingredients_entities

def get_features(raw):
    features = {
        'title':'', 
        'tei_formated_date':'', 
        'translation':'', 
        'note': '',
        'volume':'', 
        'chapter':'', 
        'entry':'', 
        'idno':'', 
        'ingredients':'',
        'utensils':'',
        'productionMethods':'',
    }
    soup = bs(raw, "lxml")
    #0 title
    features['title']=''
    features['title'] = soup.find('title').text

    #1 tei_formatted_date
    features['tei_formated_date'] = ''
    declared_date = parse(soup.find('pubdate').text)
    features['tei_formated_date'] = f'{declared_date.year}-{declared_date.month:02d}-{declared_date.day}' 

    #2 translation
    features['translation'] = ''
    trans_pos1 = raw.find('<wp:meta_key>translation</wp:meta_key>\n<wp:meta_value>')
    if trans_pos1 != -1:
        trans_pos2 = raw.find('</wp:meta_value>', trans_pos1)
        features['translation'] = raw[trans_pos1+54:trans_pos2]

    #3 anmerkungen
    features['note'] = ''
    note_pos1 = raw.find('<wp:meta_key>anmerkungen</wp:meta_key>\n<wp:meta_value>')
    if note_pos1 != -1:
        note_pos2 = raw.find('</wp:meta_value>', note_pos1)
        features['note'] = raw[note_pos1+54:note_pos2]
       

    #4 volume, #5 chapter and #6 entry
    number = ''
    number_pos1 = raw.find('<wp:meta_key>number</wp:meta_key>\n<wp:meta_value>')
    if number_pos1 != -1:
        number_pos2 = raw.find('</wp:meta_value>', number_pos1)
        number = raw[number_pos1+49:number_pos2]
    features['volume'] = number
    features['chapter'] = number
    features['entry'] = number

    #7 idno
    features['idno'] = 0
    features['idno'] = soup.find('guid').text[soup.find('guid').text.find('p=')+2:]

    #8 Zutaten, #9 MaterielleKultur and #10 diaetetik
    features['ingredients'] = ''
    features['utensils'] = ''
    features['productionMethod'] = ''
    objects = soup.findAll('category')
    
    for obj in objects:
        if obj['domain'] == 'Zutaten':
            features['ingredients'] = features['ingredients'] + \
                '\n\t\t<object type="ingredient" xml:id="{}">{}</object>\n\t\t\t'.format(obj['nicename'], obj.text)
            
        elif obj['domain'] == 'MaterielleKultur':
            features['utensils'] = features['utensils'] + \
                '\n\t\t<object type="MaterielleKultur" xml:id="{}">{}</object>\n\t\t\t'.format(obj['nicename'], obj.text)
            
        elif obj['domain'] == 'Diaetetik':
            features['productionMethod'] = features['productionMethod'] + \
                '\n\t\t<object type="Diaetetik" xml:id="{}">{}</object>\n\t\t\t'.format(obj['nicename'], obj.text)
    
    if features['ingredients']:
        features['ingredients'] = features['ingredients'][:-4]
        
    if features['utensils']:
        features['utensils'] = features['utensils'][:-4]
        
    if features['productionMethod']:
        features['productionMethod'] = features['productionMethod'][:-4]
            
    return features

def fill_recipe_template(features):
    recipe_template_path = os.path.join('.', 'templates', 'recipe_template.xml')
    expected_keys = ['title', 
                     'tei_formated_date', 
                     'translation', 
                     'note',
                     'volume', 
                     'chapter', 
                     'entry', 
                     'idno', 
                     'ingredients',
                     'utensils',
                     'productionMethods',
                     'recipe']
    
    for key in expected_keys:
        if not key in features:
            raise Exception(f'Missing key : {key}')
    
    with open(recipe_template_path, 'r') as f:
        template_xml = f.read()
    xml = et.fromstring(template_xml)
    namespaces = {'xmlns': "http://www.tei-c.org/ns/1.0"}
    
    # titles
    for e in xml.xpath('.//xmlns:title', namespaces=namespaces):
        e.text = features['title']
    
    # alt title
    for e in xml.xpath('.//xmlns:title[@type="alt"]', namespaces=namespaces):
        e.text = features['translation']
        
    # translation date
    for e in xml.xpath('.//xmlns:date[@when]', namespaces=namespaces):
        e.text = features['tei_formated_date']

    # note
    for e in xml.xpath('.//xmlns:note', namespaces=namespaces):
        e.text = features['note']
        
    # volume
    for e in xml.xpath('.//xmlns:biblScope[@unit="volume"]', namespaces=namespaces):
        e.text = features['volume']
        
    # chapter
    for e in xml.xpath('.//xmlns:biblScope[@unit="chapter"]', namespaces=namespaces):
        e.text = features['chapter']
        
    # entry
    for e in xml.xpath('.//xmlns:biblScope[@unit="entry"]', namespaces=namespaces):
        e.text = features['entry']
        
    # idno
    for e in xml.xpath('.//xmlns:biblScope[@unit="idno"]', namespaces=namespaces):
        e.text = features['idno']
    
    for e in xml.xpath('.//xmlns:div[@type="ingredient"]/xmlns:listObject', namespaces=namespaces):
        e.text = features['ingredients']
        
    # utensils
    for e in xml.xpath('.//xmlns:div[@type="utensil"]/xmlns:listObject', namespaces=namespaces):
        e.text = features['utensils']
        
    # production method
    for e in xml.xpath('.//xmlns:div[@type="dietetic"]/xmlns:listObject', namespaces=namespaces):
        e.text = features['productionMethods']
        
    # production method
    for e in xml.xpath('.//xmlns:div[@type="recipe"]/xmlns:p', namespaces=namespaces):
        e.text = features['recipe']
    
    return et.tounicode(xml)