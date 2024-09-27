import csv
import datetime
import os

#Speichert die Liste als Tabelle in einer CSV-Datei.
def save_as_table(data, filename:str):
    # Namen der Spalten
    fieldnames = data[0].keys()

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
        # Schreibe die Spaltenüberschriften
        writer.writeheader()

        # Schreibe die Daten
        for row in data:
            writer.writerow(row)

#Liest eine Tabelle aus einer CSV-Datei und gibt eine Liste von Dictionaries zurück. Eingabeparamter als String.
def read_from_table(filename:str):
    data = []
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        # Lesen der Daten Zeile für Zeile
        for row in reader:
            row['Chipnummer'] = int(row['Chipnummer'])
            data.append(dict(row))
    return data

#Fügt einen User hinzu
def add_user(chipcode:int, username:str):
    data = read_from_table("daten.csv")
    user_in_list = chipcode_in_data(chipcode)
    if {"Chipnummer": int(chipcode), "Benutzername": username} not in data and user_in_list == False:
        data.append({"Chipnummer": chipcode, "Benutzername": username, "Letzter Login": None})
        # Speichere die Daten als Tabelle in der Datei
        filename = "daten.csv"
        save_as_table(data, filename)
        #Vermerkt es in der Logdatei
        log_write("Benutzer " +username+ " mit Chipcode: " +str(chipcode)+" wurde hinzugefuegt.")

#löscht einen Benutzer anhand seines chipcodes
def delete_user(chipcode:int):
    data = read_from_table("daten.csv")
    username = user_in_data(chipcode)
    for code in data:
        realnumber = code["Chipnummer"]
        if realnumber == chipcode:
            data.remove(code)
            # Speichere die Daten als Tabelle in der Datei
            filename = "daten.csv"
            save_as_table(data, filename)
            log_write("Benutzer " +username+ " mit Chipcode: " +str(chipcode)+" wurde gelöscht.")

#Funktion sucht ob sich der Chipcode in der Datei befindet
def chipcode_in_data(chipcode:int)->bool:
    data = read_from_table("daten.csv")
    for code in data:
        realnumber = code["Chipnummer"]
        if realnumber == chipcode:
            return True
    return False

#Funktion sucht enstrepchenden Benutzername zu dem Chipcode raus
def user_in_data(chipcode:int)->str:
    data = read_from_table("daten.csv")
    for code in data:
        realnumber = code["Chipnummer"]
        if realnumber == chipcode:
            return code["Benutzername"]

#Funktion die das letzte Login_Datum eines Benutzers in die Excel_Datei schreibt
def login_write(chipcode:int):
    #holt sich die aktuelle Uhrzeit und wandelt es um das es nur noch bis Minuten anzeigt
    date = datetime.datetime.now()
    date = date.strftime("%Y-%m-%d %H:%M") 
    #liest Datei ein
    data = read_from_table("daten.csv")
    index = 0
    for code in data:
        realnumber = code["Chipnummer"]
        if realnumber == chipcode:
            code["Letzter Login"] = date
            data.remove(code)
            data.insert(index,code)
        index += 1
    # Speichere die Daten als Tabelle in der Datei
    filename = "daten.csv"
    save_as_table(data, filename)
    


# Schreibt in die Logdatei
def log_write(what_was_done: str):
    # Aktuelle Datum und Uhrzeit erhalten
    aktuelle_zeit = datetime.datetime.now()
    zeit_als_string = aktuelle_zeit.strftime("%H:%M:%S")
    datum_als_string = aktuelle_zeit.strftime("%Y-%m-%d")
    # Formatieren des Eintrags
    log_entry = f"{datum_als_string} {zeit_als_string}: {what_was_done}\n"
    # Lesen des aktuellen Inhalts der Logdatei
    with open("logdatei.txt", "r+") as logdatei:
        # Lesen des bisherigen Inhalts der Logdatei
        existing_content = logdatei.read()
        # Zurücksetzen des Dateizeigers auf den Anfang
        logdatei.seek(0)
        # Schreiben des neuen Eintrags an den Anfang der Datei
        logdatei.write(log_entry)
        # Schreiben des bisherigen Inhalts nach dem neuen Eintrag
        logdatei.write(existing_content)

#löscht nach 30 Tagen die Zeile in der Logdatei und verschiebt es in die Longlogdatei, die kann später ausgewertet werden wenn man möchte.
def separte_logdata():
    longlogdatei = "longlogdatei.txt"
    logdatei = "logdatei.txt"
    # Aktuelles Datum erhalten
    aktuelles_datum = datetime.date.today()
    # Ein Monat entspricht etwa 30 Tagen
    ein_monat = datetime.timedelta(days=30)
    # Öffnen der Logdatei zum Lesen
    with open(logdatei, "r",encoding='windows-1252') as log, open(longlogdatei, "a") as longlogdatei_tmp, open("temp.log", "a") as temp:
         for zeile in log:
            # Überprüfen, ob die Zeile mindestens ein Leerzeichen enthält
            if ' ' not in zeile:
                continue          
            # Die erste Spalte der Zeile ist das Datum im Format "YYYY-MM-DD"
            datum_string = zeile.split()[0]
            datum = datetime.datetime.strptime(datum_string, "%Y-%m-%d").date()          
            # Überprüfen, ob das Datum älter als ein Monat ist
            if aktuelles_datum - datum > ein_monat:
                # Wenn ja, die Zeile in die separate Datei schreiben
                longlogdatei_tmp.write(zeile)
            else:
                # Wenn nein, die Zeile in eine temporäre Datei schreiben
                temp.write(zeile)
    # Die ursprüngliche Logdatei mit den übrigen Zeilen überschreiben
    os.replace("temp.log", logdatei)

