import os
import shutil
import datetime
import pprint
import plistlib
import xml.etree.ElementTree as ET

#Where to backup on the Mac - desktop by default
backup_dir = '~/Desktop/Ubackup/'

#Ulysses backup files
Ulysses_backup_dir = '~/Library/Group Containers/X5AZV975AG.com.soulmen.shared/Ulysses/Backups/'

#Ulysses files
Ulysses_dir = '~/Library/Mobile Documents/X5AZV975AG~com~soulmen~ulysses3/Documents'

backup_dir = os.path.expanduser(backup_dir)

current_date = datetime.datetime.now()
formatted_date = current_date.strftime("%Y%m%d-%H%M")
markdown_dir = os.path.join(backup_dir, f"markdown-{formatted_date}/")
Ulysses_backup_dir = os.path.expanduser(Ulysses_backup_dir)
Ulysses_dir = os.path.expanduser(Ulysses_dir)

#Init
tag_to_md = {}
cache_noms_dossiers = {}

def secure_backup():

    current_date = datetime.date.today()
    formatted_date = current_date.strftime("%Y%m%d")
    last_backup = os.path.join(Ulysses_backup_dir, "Latest Backup.ulbackup")
    
    if os.path.exists(last_backup):
        last_backup_target = os.path.join(backup_dir, f"ulysses-{formatted_date}.ulbackup")
        shutil.copytree(last_backup, last_backup_target, dirs_exist_ok=True)
    else:
        print("No Ulysses backup found!")

#Decode Ulysses tag structure
def build_tag_mapping(root):
    tag_to_md = {}
    for tag in root.findall(".//tag"):
        definition = tag.get('definition')
        pattern = tag.get('pattern')
        startPattern = tag.get('startPattern')
        endPattern = tag.get('endPattern')

        if startPattern and endPattern:
            tag_to_md[definition] = (startPattern, endPattern)
        elif pattern:
            tag_to_md[definition] = pattern

    return tag_to_md


def process_elementOld(element):
    global tag_to_md

    text = ''

    # Traitement du texte directement dans l'élément
    if element.text:
        text += element.text

    # Traitement récursif des sous-éléments
    for child in element:
        if child.tag in ['tag', 'element']:
            kind = child.get('kind')
            md_pattern = tag_to_md.get(kind, ('', ''))

            # Appliquer le pattern de début
            text += md_pattern[0] if isinstance(md_pattern, tuple) else md_pattern

            # Traitement récursif pour les sous-éléments
            text += process_element(child)

            # Appliquer le pattern de fin
            text += md_pattern[1] if isinstance(md_pattern, tuple) else ''

        # Ajouter le texte après le sous-élément (tail)
        if child.tail:
            text += child.tail

    return text.strip()


def process_element(element):
    text = ''

    # Traitement du texte directement dans l'élément
    if element.text:
        text += element.text

    # Traitement récursif des sous-éléments
    for child in element:
        if child.tag == 'tag':
            # Ajouter le texte du tag
            if child.text:
                text += child.text

        # Pour les balises <element>
        elif child.tag == 'element':
            start_tag = child.get('startTag') or ''
            end_tag = child.get('endTag') or ''
            element_text = child.text or ''

            # Ajouter le formatage Markdown et le texte de l'élément
            text += start_tag + element_text + end_tag

        # Ajouter le texte après le sous-élément (tail)
        if child.tail:
            text += child.tail

    return text.strip()

def convert_ulysses_to_markdown(xml_content):
    global tag_to_md

    root = ET.fromstring(xml_content)

    if len(tag_to_md) == 0:
        tag_to_md = build_tag_mapping(root)

    markdown = ""
    for p in root.iter('p'):
        markdown += process_element(p) + '\n\n'

    return markdown.strip()

def build_md_path(filename):
    global saved_path    
    md_file= os.path.join(markdown_dir,saved_path,filename+".md")
    destination_dir = os.path.dirname(md_file)
    os.makedirs(destination_dir, exist_ok=True)
    return md_file


def analyser_ulgroup(file):
    # Vérifier si le résultat est déjà dans le cache
    if file in cache_noms_dossiers:
        return cache_noms_dossiers[file]

    try:
        with open(file, 'rb') as f:
            contenu = plistlib.load(f)
            nom_dossier = contenu.get('displayName', 'Nom Inconnu')
            cache_noms_dossiers[file] = nom_dossier  # Sauvegarder dans le cache
            return nom_dossier
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {fichier}: {e}")
        return 'Nom Inconnu'

def real_dir_names(file):
    # Diviser le chemin et extraire les noms
    segments = file.split('/')
    noms_dossiers = []

    for segment in segments:
        if segment.endswith('-ulgroup'):
            fichier_ulgroup = os.path.join('/'.join(segments[:segments.index(segment) + 1]), 'Info.ulgroup')
            nom_dossier = analyser_ulgroup(fichier_ulgroup)
            noms_dossiers.append(nom_dossier)

    return "/".join(noms_dossiers)

def get_order(fichier):
    try:
        with open(fichier, 'rb') as file:
            contenu = plistlib.load(file)
            if len(contenu)>0:
                print(contenu)
            # Obtenir l'ordre des enfants
            ordre = contenu.get('childOrder', [])
            return ordre
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {fichier}: {e}")
        return []
    
def sort_files(filename):
    if filename.endswith('.ulgroup'):
        return (0, filename)
    elif filename.endswith('.plist'):
        return (1, filename)
    else:
        return (2, filename)
    
os.system('clear')

#secure_backup()

data_file_extensions = {'.png', '.jpg', '.jpeg', '.tiff'}
total_txt = 0
total_xml = 0
total_empty = 0
saved_path = ""
content_index = 0

for dirpath, dirnames, filenames in os.walk(Ulysses_dir):

    # Trier les fichiers pour que .ulgroup soient traités en premier
    #filenames.sort(key=lambda f: (not f.endswith('.ulgroup'), f))

    # Trier les fichiers pour que .ulgroup soient traités en premier, puis .plist
    filenames.sort(key=sort_files)

    for filename in filenames:

        # Construire le chemin complet du fichier
        filepath = os.path.join(dirpath, filename)

        if filename.startswith('.'):
            continue

        elif filename.endswith('.txt'):
            #Pure mardown file (but not allway there, therefore not usable)
            total_txt += 1

        elif filename.endswith('.xml'):
            #XML Ulysses Markdown
            total_xml += 1

            with open(filepath) as f:
                xml = f.read()
            
            markdown = convert_ulysses_to_markdown(xml)
            if len(markdown)>0:

                content_index +=1
                md_file = build_md_path(f"content{content_index}")
                print(md_file)
                
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                
            else:
                #Empty sheet
                total_empty += 1

        elif filename.endswith('.ulgroup'):
            #Plist file
            saved_path = real_dir_names(filepath)
            content_index = 0

        elif filename.endswith('.plist'):
            #File versioning
            pass

        elif os.path.splitext(filename)[1].lower() in data_file_extensions:
            #Images, PDF and other files attached to projects
            pass
   
        else:
            #Trash
            continue

print("txt:",total_txt)
print("xml:",total_xml)
print("empty xml:",total_empty)