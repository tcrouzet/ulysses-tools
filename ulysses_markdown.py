import xml.etree.ElementTree as ET
import re
import pprint
import os

footnote_index = 1
footnote_text = ""

def process_element(element,pattern,order):
    global footnote_index,footnote_text,element_attribute

    text = ''
    attribute = ''

    # Traitement du texte directement dans l'élément
    if element.text:
        text += element.text

    # Traitement récursif des sous-éléments
    for child in element:

        if child.tag in ['tags', 'tag']:
            (tag_text, _) = process_element(child,pattern,order)
            text += tag_text+" "

        # Pour les balises <element>
        elif child.tag == 'element':

            kind = child.get('kind')

            if kind=="footnote":
                footnote_detail = child.find('.//string')
                if footnote_detail is not None:
                    footnote_text_here = ""
                    for para in footnote_detail:
                        if para.tag == 'p':
                            (para_text, _) = process_element(para, pattern, order)
                            footnote_text_here += para_text
                            #footnote_text_here += ''.join(para.itertext()).strip()

                    if footnote_text_here:
                        text += f"[^{footnote_index}]"
                        footnote_text += f"[^{footnote_index}] {footnote_text_here}\n\n"
                        footnote_index += 1
                        element_attribute = ""

            elif kind=="image":
                element_attribute = ""
                image_attribute = child.find(".//attribute[@identifier='image']")
                if image_attribute is not None:
                    alt_attribute = child.find(".//attribute[@identifier='description']")
                    if alt_attribute is not None:
                        alt = alt_attribute.text
                    else:
                        alt = "Image"
                    text += f"![{alt}](media-{order}/{image_attribute.text})"

            elif pattern[kind]["start"] and pattern[kind]["end"]:

                (element_text, element_attribute) = process_element(child,pattern,order)
                text += pattern[kind]["start"] + element_text + pattern[kind]["end"]

            elif pattern[kind]["pattern"]:

                text += pattern[kind]["pattern"]

            if element_attribute:
                text += f"({element_attribute})"

        elif child.tag == 'attribute' and child.text:

            identifier = child.get('identifier')
            if identifier in ["URL"]:
                attribute = child.text

        # Ajouter le texte après le sous-élément (tail)
        if child.tail:
            text += child.tail

    return (text,attribute)


def ulysses_to_markdown(xml_content,order):
    global footnote_text,footnote_index

    footnote_index = 1
    footnote_text = ""

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
    parent_map = {c: p for p in root.iter() for c in p}
    for p in root.iter('p'):
        parent = parent_map.get(p)
        if parent == root or parent_map.get(parent) == root:
            (text,_) = process_element(p,pattern,order)
            markdown += text + '\n\n'
    markdown += footnote_text
    markdown = re.sub(r' {2,}', ' ', markdown)
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)

    return (markdown.strip(),attachment_html.strip())

def get_filename(markdown_text):

    # Supprimer les lignes de tirets
    markdown_text = markdown_text[:256]
    markdown_text = re.sub(r'^-+\n?', '', markdown_text, flags=re.MULTILINE)
    markdown_text = markdown_text.replace("#",'')
    markdown_text = markdown_text.replace("*",'')
    markdown_text = markdown_text.strip()

    # Supprimer les balises Markdown
    markdown_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', markdown_text)  # Supprimer les liens
    markdown_text = re.sub(r'[_*#>`]', '', markdown_text)  # Supprimer les autres balises Markdown
    markdown_text = re.sub(r'\([^)]*\)', '', markdown_text)
    markdown_text = re.sub(r'[\\/*?:"<>|]', '', markdown_text)  # Supprimer les caractères non valides
    markdown_text = markdown_text.strip().replace(' ', '_')  # Remplacer les espaces par des underscores
    markdown_text = markdown_text.replace("_-_","_")
    markdown_text = markdown_text.replace(",","\n")
    markdown_text = markdown_text.replace(".","\n")
    
    lines = markdown_text.split('\n')
    for line in lines:
        if line.strip():
            line = line[:48]
            line = line.lower()
            return line.strip()

    return "unknown"

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
        pprint.pprint(ulysses_to_markdown(xml,"00"))

md_test()

md ="""## 

(img)

La lutte contre les infections liées aux soins, particulièrement l’hygiène des mains, tout comme ce livre qui la raconte, bénéficient du soutien particulier de bioMérieux, B. Braun Medical, Hong Kong Infection Control Nurses’ Association, Laboratoires Anios, SARAYA et du POPS (Private Organizations for Patient Safety), une association qui a pour but de promouvoir la sécurité des patients à l’échelle globale en étroite collaboration avec l’Organisation Mondiale de la Santé et qui regroupe notamment B. Braun Medical, Deb Group (Ltd./DebMed USA), LLC, Ecolab, Elyptol, GeneralSensing, GOJO, Hartmann Group – Bode Science Centre, Laboratoires Anios, SARAYA, Sealed Air, Schulke et Surewash."""

#print(get_filename(md))