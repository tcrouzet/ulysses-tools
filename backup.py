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
markdown_dir = os.path.join(backup_dir, "markdown/")
Ulysses_backup_dir = os.path.expanduser(Ulysses_backup_dir)
Ulysses_dir = os.path.expanduser(Ulysses_dir)
tag_to_md = {}

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


def process_element(element):
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

def build_path(filepath,search,replace):
    path = filepath.replace(Ulysses_dir+"/", '')
    md_file= os.path.join(markdown_dir,path)
    md_file= md_file.replace(search,replace)
    destination_dir = os.path.dirname(md_file)
    os.makedirs(destination_dir, exist_ok=True)
    return md_file

os.system('clear')

#secure_backup()

data_file_extensions = {'.png', '.jpg', '.jpeg', '.tiff'}
total_txt=0
total_xml=0
total_empty=0

for dirpath, dirnames, filenames in os.walk(Ulysses_dir):

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

                md_file = build_path(filepath,"ulysses/Content.xml","md")
                with open(md_file, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                
            else:
                #Empty sheet
                total_empty += 1
                #xml_file = build_path(filepath,"","")
                #shutil.copy2(filepath, xml_file)
                #pprint.pprint(filepath)
                #pprint.pprint(xml_file)
                pass

        elif filename.endswith('.ulgroup'):
            #Prorietary file (this is very wrong)
            vide_file = build_path(filepath,".ulgroup","-vide.txt")
            with open(vide_file, 'w') as fi:
                pass 
            #with open(filepath) as f:
            #    temptext = f.read()
            #pprint.pprint(temptext)
            #exit()
            pass

        elif filename.endswith('.plist'):
            #activityHistory not very usefull for backup

            continue
            with open(filepath, 'rb') as f:
                plist_data = plistlib.load(f)
            pprint.pprint(plist_data)

        elif os.path.splitext(filename)[1].lower() in data_file_extensions:
            #Images, PDF and other files attached to projects
            pass
   
        else:
            #Trash
            continue

print("txt:",total_txt)
print("xml:",total_xml)
print("empty xml:",total_empty)