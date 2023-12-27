import xml.etree.ElementTree as ET
import re
import pprint
import os

def process_element(element,pattern):
    text = ''
    attribute = ''

    # Traitement du texte directement dans l'élément
    if element.text:
        text += element.text

    # Traitement récursif des sous-éléments
    for child in element:

        if child.tag == 'tags' or child.tag == 'tag':
            (tag_text, _) = process_element(child,pattern)
            text += tag_text+" "

        # Pour les balises <element>
        elif child.tag == 'element':

            kind = child.get('kind')
            #pprint.pprint(kind)
            #pprint.pprint(pattern[kind])
            (element_text, element_attribute) = process_element(child,pattern)

            if pattern[kind]["start"] and pattern[kind]["end"]:
                text += pattern[kind]["start"] + element_text + pattern[kind]["end"]
            elif pattern[kind]["pattern"]:
                text += pattern[kind]["pattern"]

            if element_attribute:
                text += f"({element_attribute})"

        elif child.tag == 'attribute' and child.text:
            attribute = child.text

        # Ajouter le texte après le sous-élément (tail)
        if child.tail:
            text += child.tail

    return (text,attribute)

def ulysses_to_markdown(xml_content):

    root = ET.fromstring(xml_content)

    pattern = ulysses_pattern(root)
    #pprint.pprint(pattern)

    attachment_html = ""
    for attachment in root.iter('attachment'):
        attachment_html += "<attachment"
        for key, value in attachment.attrib.items():
            attachment_html += f' {key}="{value}"'
        attachment_html += '>'

        for child in attachment:
            attachment_html += ET.tostring(child, encoding='unicode')
        
        attachment_html += '</attachment>\n'

    # Supprimer tous les éléments <attachment>
    xml_min = re.sub(r'<attachment[^>]*>.*?</attachment>', '', xml_content, flags=re.DOTALL)
    root = ET.fromstring(xml_min)
    
    markdown = ""
    for p in root.iter('p'):
        (text,_) = process_element(p,pattern)
        markdown += text + '\n\n'
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)

    return (markdown.strip(),attachment_html.strip())

def get_filename(markdown_text):

    # Supprimer les lignes de tirets
    markdown_text = re.sub(r'^-+\n?', '', markdown_text, flags=re.MULTILINE)

    # Extraire le premier paragraphe non vide
    paragraphs = markdown_text.strip().split('\n\n')
    first_paragraph = next((p for p in paragraphs if p.strip()), "")

    # Supprimer les balises Markdown
    text_only = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', first_paragraph)  # Supprimer les liens
    text_only = re.sub(r'[_*#>`]', '', text_only)  # Supprimer les autres balises Markdown

    # Prendre les 128 premiers caractères
    filename = text_only[:64]

    # Nettoyer pour obtenir un nom de fichier valide
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)  # Supprimer les caractères non valides
    filename = filename.strip().replace(' ', '_')  # Remplacer les espaces par des underscores
    filename = filename.replace("_-_","_")

    return filename.lower()

def ulysses_pattern(root):
    # Trouvez la section markup
    markup = root.find('markup')

    # Dictionnaire pour stocker les informations des balises
    tag_info = {}

    # Extraire les balises et leurs patterns
    tags = markup.findall('tag')
    for tag in tags:
        definition = tag.get('definition')
        pattern = tag.get('pattern', None)
        startPattern = tag.get('startPattern', None)
        endPattern = tag.get('endPattern', None)
        
        # Stockez les informations dans le dictionnaire
        tag_info[definition] = {
            "pattern": pattern,
            "start": startPattern,
            "end": endPattern
        }
    
    return tag_info

def md_test():
    os.system('clear')
    with open("samples/source.xml") as f:
        xml = f.read()
        pprint.pprint(ulysses_to_markdown(xml))

md_test()