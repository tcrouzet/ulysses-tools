import os
import shutil
import datetime
import plistlib
import xml.etree.ElementTree as ET
import json
from config import backup_dir, Ulysses_dir, uHide
import ulysses_markdown as md

current_date = datetime.datetime.now()
formatted_date = current_date.strftime("%Y%m%d-%H%M")
markdown_dir = os.path.join(backup_dir, f"markdown-{formatted_date}/")

def build_path(filename,ext=".md"):
    global saved_path    
    md_file= os.path.join(markdown_dir,saved_path,filename+ext)
    destination_dir = os.path.dirname(md_file)
    os.makedirs(destination_dir, exist_ok=True)
    return md_file

def update_saved_path(id,flag):
    global saved_path

    if flag:
        # Remplacer le dernier segment du chemin par l'identifiant
        path_parts = saved_path.split(os.sep)[:-1]  # Enlever le dernier segment
        path_parts.append(id)
        saved_path = os.sep.join(path_parts)
    else:
        saved_path = os.path.join(saved_path, id)

def analyser_ulgroup(file):
    global cache_noms_dossiers

    # Vérifier si le résultat est déjà dans le cache
    if file in cache_noms_dossiers:
        return cache_noms_dossiers[file]

    contenu = plist_loader(file)
    if contenu:
        nom_dossier = contenu.get('displayName', 'Nom Inconnu')
        child_order = contenu.get('childOrder', [])
        cache_noms_dossiers[file] = (nom_dossier, child_order)
        return (nom_dossier, child_order)
    else:
        return ('Unknown Name', [])

def real_dir_names(file):
    # Diviser le chemin et extraire les noms
    segments = file.split('/')
    noms_dossiers = []
    ordre_dossier = {}

    for segment in segments:
        if segment.endswith('-ulgroup'):
            fichier_ulgroup = os.path.join('/'.join(segments[:segments.index(segment) + 1]), 'Info.ulgroup')
            nom_dossier, child_order = analyser_ulgroup(fichier_ulgroup)

            # Calculer la longueur nécessaire pour le formatage
            max_length = len(str(len(child_order)))

            ordre_dossier.update({d: str(index + 1).zfill(max_length) for index, d in enumerate(child_order)})
            prefixe_ordre = ordre_dossier.get(segment, "0" * max_length)
            noms_dossiers.append(f"{prefixe_ordre}-{nom_dossier}")


    return "/".join(noms_dossiers)

def plist_loader(path):
    global plist_cache,plist_file_bugs

    # Vérifier si le résultat est déjà dans le cache
    if path in plist_cache:
        return plist_cache[path]

    try:
        with open(path, 'rb') as f:
            contenu = plistlib.load(f)
            plist_cache[path] = contenu
            return contenu

    except Exception as e:
        plist_file_bugs += 1
        plist_cache[path] = ""
        #print(f"Error reading file {path}: {e}")
        return False

def metadata_id(path):
    path = path.replace("/Metadata.plist", "")
    path = path.replace("/TextChecker.plist","")
    temp_id = os.path.basename(path)
    if temp_id == "":
        print("No id found",path)
    return temp_id

#Input XML file
def find_order_id_timestamps(filepath):
    xml_dir = os.path.dirname(filepath)
    metadata_file = os.path.join(xml_dir,"Metadata.plist")
    timestamps = find_timestamps(metadata_file)
    id = os.path.basename(xml_dir)
    #print(id)
    parent_dir = os.path.dirname(xml_dir)
    #print(parent_dir)
    plist_file = os.path.join(parent_dir,"Info.ulgroup")
    #print(plist_file)
    ulgroup_data = plist_loader(plist_file)

    if "sheetClusters" in ulgroup_data:
        total_length = len(ulgroup_data["sheetClusters"])
        max_digits = len(str(total_length))

        for i, cluster in enumerate(ulgroup_data["sheetClusters"]):
            if id in cluster:
                return (str(i + 1).zfill(max_digits),id,timestamps)

    print(f"No {id} in SheetCluster")
    return ("xxx",id,timestamps)

def date_2_timestamp(date_str):
    try:     
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        date_obj = datetime.datetime.now()
    return int(date_obj.timestamp())

def find_timestamps(filepath):
    plist_data = plist_loader(filepath)
    if plist_data and "activityHistory" in plist_data and plist_data["activityHistory"]:
        activity_history = plist_data["activityHistory"]
        first_date = activity_history[0]["date"]
        last_date = activity_history[-1]["date"]
        return (date_2_timestamp(first_date), date_2_timestamp(last_date))
    else:
        return (int(datetime.datetime.now().timestamp()), int(datetime.datetime.now().timestamp()))
    
def add_directory_to_path(path, new_directory):
    directory, filename = os.path.split(path)
    news_dir_path = os.path.join(directory, new_directory)
    os.makedirs(news_dir_path, exist_ok=True)
    return os.path.join(news_dir_path, filename)

def process_file(filepath):
    global total_txt, total_xml, total_empty, saved_path, order, id

    filename = os.path.basename(filepath)

    if filename.startswith('.'):
        pass

    elif filename.endswith('.txt'):
        #Pure mardown file (but not often there, therefore not usable)
        total_txt += 1

    elif filename.endswith('.xml'):
        #XML Ulysses Markdown
        total_xml += 1

        with open(filepath, encoding='utf-8') as f:
            xml = f.read()
        
        (order,id,timestamps) = find_order_id_timestamps(filepath)
        (markdown,attachement) = md.ulysses_to_markdown(xml, order, uHide)
        if len(markdown)>0:
            md_filename = md.get_filename(markdown)
            md_file = build_path(f"{order}-{md_filename}")
            #md_file = build_path(f"{order}-{id}-{md_filename}")
            while os.path.exists(md_file):
                md_file = md_file.replace(".md","0.md")     

            #Ulysses tags, notes, goals… in comment
            if len(attachement)>0:
                markdown = f"{markdown}\n\n<!--{attachement}-->"

            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(markdown)
                os.utime(md_file, timestamps)

            #Save source file
            source_file = add_directory_to_path(md_file, f"{uHide}sources")
            source_file = source_file.replace(".md","-ulysses.xml")
            shutil.copy2(filepath,source_file)
            
        else:
            #Empty sheet
            total_empty += 1

    elif filename.endswith('.ulgroup'):
        #Plist file describing folders and sub-folders
        ulgroup_data = plist_loader(filepath)
        if ulgroup_data:
            saved_path = real_dir_names(filepath)
            ulgroup_str = json.dumps(ulgroup_data)
            ulgroup_file = build_path(f"{uHide}Info",".json")
            with open(ulgroup_file, 'w', encoding='utf-8') as f:
                f.write(ulgroup_str)

    elif filename.endswith('.plist') and filename != 'Root.plist':
        #Metada.plist
        plist_data = plist_loader(filepath)
        if plist_data:
            plist_str = json.dumps(plist_data)
            plist_file = build_path(f"{uHide}plist/{order}",".json")
            with open(plist_file, 'w', encoding='utf-8') as f:
                f.write(plist_str)

    elif os.path.splitext(filename)[1].lower() in data_file_extensions:
        #Images, PDF and other files attached to projects
        media_file = build_path(f"{uHide}media-{order}/",filename.lower())
        media_file = media_file.replace("DraggedImage.","")
        media_file = media_file.replace("draggedimage.","")
        shutil.copy2(filepath, media_file)

    else:
        #Trash
        pass

def sort_files(filename):
    if filename.endswith('.ulgroup'):
        return (0, filename)
    elif filename.endswith('.ulysses'):
        return (1, filename)
    elif filename.endswith('.plist'):
        return (2, filename)
    elif filename.endswith('.xml'):
        return (3, filename)
    else:
        return (4, filename)

def sort_dir(filename):
    if filename.endswith('.ulysses'):
        return (0, filename)
    elif filename.endswith('-ulgroup'):
        return (1, filename)
    else:
        return (2, filename)

def custom_walk(directory):
    all_files = []
    subdirs = []

    # Collecter tous les fichiers et sous-dossiers
    for entry in os.scandir(directory):
        if entry.is_file():
            all_files.append(entry.path)
        elif entry.is_dir():
            subdirs.append(entry.path)

    # Trier et traiter tous les fichiers
    all_files.sort(key=sort_files)
    for filepath in all_files:
        #if '3c62fd89def541a3a00b1d01aa2374b4-ulgroup/Info.ulgroup' in filepath:
        #    print(plist_loader(filepath))
        process_file(filepath)

    # Parcourir récursivement les sous-dossiers
    subdirs.sort(key=sort_dir)
    for subdir in subdirs:
        custom_walk(subdir)

os.system('clear')

cache_noms_dossiers = {}
plist_cache = {}
data_file_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.pdf'}
total_txt = 0
total_xml = 0
total_empty = 0
plist_file_bugs = 0
saved_path = ""
timestamps = find_timestamps("")
id = "" #Current Ulysses file id

custom_walk(Ulysses_dir)

print("txt:",total_txt)
print("xml:",total_xml)
print("empty xml:",total_empty)
print("no plist file:",plist_file_bugs)

md.images_path(markdown_dir)