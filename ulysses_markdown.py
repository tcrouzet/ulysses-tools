import xml.etree.ElementTree as ET
import re
import pprint
import os
import unicodedata
from config import no_accent_in_file

footnote_index = 1
footnote_text = ""

def no_accent(msg):
    texte_sans_accent = unicodedata.normalize('NFKD', msg).encode('ASCII', 'ignore')
    return texte_sans_accent.decode('ASCII')

def process_element(element,pattern,order,uHide):
    global footnote_index,footnote_text,element_attribute

    text = ''
    attribute = ''

    # Traitement du texte directement dans l'élément
    if element.text:
        text += element.text

    # Traitement récursif des sous-éléments
    for child in element:

        if child.tag in ['tags', 'tag']:
            (tag_text, _) = process_element(child, pattern, order, uHide)
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
                            (para_text, _) = process_element(para, pattern, order, uHide)
                            footnote_text_here += para_text
                            #footnote_text_here += ''.join(para.itertext()).strip()

                    if footnote_text_here:
                        text += f"[^{footnote_index}]"
                        footnote_text += f"[^{footnote_index}]: {footnote_text_here}\n\n"
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
                    text += f"![{alt}]({uHide}media-{order}/{image_attribute.text})"

            elif pattern[kind]["start"] and pattern[kind]["end"]:

                (element_text, element_attribute) = process_element(child, pattern, order, uHide)
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


def ulysses_to_markdown(xml_content, order, uHide="."):
    global footnote_text,footnote_index

    footnote_index = 1
    footnote_text = ""

    root = ET.fromstring(xml_content)

    pattern = ulysses_pattern(root)
    #pprint.pprint(pattern)

    # Supprimer tous les éléments <attachment>
    #xml_min = re.sub(r'<attachment[^>]*>.*?</attachment>', '', xml_content, flags=re.DOTALL)
    #root = ET.fromstring(xml_min)
    
    markdown = ""
    parent_map = {c: p for p in root.iter() for c in p}
    for p in root.iter('p'):
        parent = parent_map.get(p)
        if parent == root or parent_map.get(parent) == root:
            (text,_) = process_element(p, pattern, order, uHide)
            markdown += text + '\n\n'
    markdown += footnote_text
    markdown = re.sub(r' {2,}', ' ', markdown)
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)

    bad_jumps = re.compile(u'[\u2028\u2029\u0085]')
    markdown = bad_jumps.sub('\n', markdown)
    #markdown = markdown.replace("---- \n","---\n")
    markdown = markdown.strip()

    special_tags = ["keywords","note","goal"]
    attachment_html = ""
    keywords = ""
    note = ""
    for attachment in root.iter('attachment'):
        attachment_tmp = ""
        for key, value in attachment.attrib.items():
            #print(key, value)
            if value not in special_tags:
                attachment_tmp += f' {key}="{value}"'
            else:
                break
        if attachment_tmp:
            attachment_tmp = "<attachment"+attachment_tmp+'>'

        if list(attachment):
            for child in attachment:
                string_tmp = ET.tostring(child, encoding='unicode')
                if value not in special_tags:
                    attachment_tmp += string_tmp
                elif value=="note":
                    note += re.sub(r'<[^>]+>', '', string_tmp).strip()
        else:
            if attachment.text:
                if value == "keywords":
                    keywords+= attachment.text
                    attachment_tmp = ""
                else:
                    attachment_tmp += attachment.text
        
        if attachment_tmp:
            attachment_html += attachment_tmp+'</attachment>\n'

    if keywords:
        keywords = "#" + keywords.replace(","," #")
        markdown += f"\n\n{keywords}"

    if note:
        markdown += f"\n<!--{note}-->"

    return (markdown.strip(),attachment_html.strip())

def get_filename(markdown_text):
    global no_accent_in_file

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
            if no_accent_in_file:
                line = no_accent(line)
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
        if definition not in tag_info:
            if definition == "divider":
                pattern = "---"
            tag_info[definition] = {
                "pattern": pattern,
                "start": startPattern,
                "end": endPattern
            }
    
    return tag_info

def images_path(root_dir):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']

    images_count = 0
    md_modifiy = 0
    md_count =0

    for root, dirs, files in os.walk(root_dir):

        image_files = [f for f in files if any(f.endswith(ext) for ext in image_extensions)]
        
        if image_files:

            images_count += len(image_files)

            # Move up one directory level
            filepath = os.path.join(root, image_files[0])
            parts = filepath.split(os.sep)
            media_dir = parts[-2]
            if "-" in media_dir:
                (_,order) = media_dir.split("-")
            else:
                order = media_dir
            #print(order)
            parent_dir = os.path.dirname(root)
            #print(parent_dir)

            md_files = [f for f in os.listdir(parent_dir) if f.endswith('.md') and f.startswith(order)]

            for md_file in md_files:
                md_count += 1
                md_file_path = os.path.join(parent_dir, md_file)
                with open(md_file_path, 'r', encoding='utf-8') as file:
                    md_content = file.read()
                    #print(md_content)
                    #exit()
                    md_org = md_content
                    for image_file in image_files:
                        name_without_extension = image_file.rsplit('.', 1)[0]
                        #print(image_file)
                        code = name_without_extension.split('.')[-1]
                        #print(code)
                        md_content = md_content.replace(code,image_file)
                    if md_org != md_content:
                        md_modifiy += 1
                        with open(md_file_path, 'w', encoding='utf-8') as f:
                            f.write(md_content)

    print("Images:",images_count)
    print("Markdown file to update:",md_count)
    print("Markdown image updates:",md_modifiy)

def md_test():
    os.system('clear')
    with open("samples/source.xml") as f:
        xml = f.read()
        pprint.pprint(ulysses_to_markdown(xml,"00"))

md_test()