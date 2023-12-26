import os
import json
import datetime

os.system('clear')

with open("info.json", 'r') as file:
    data = json.load(file)

    # Compter le nombre de sheetClusters
    count = len(data["resolutionData"]["sheetClusters"])
    print(count)

    count = len(data["sheetClusters"])
    print(count)

    #timestamp = data["resolutionData"]["sheetClusters"]["c3347c7496d3429f95934dde75c89c61.ulysses"]["lastModification"])
    timestamp = 725222177.345358
    date_time = datetime.datetime.fromtimestamp(timestamp)
    print(date_time)
