from werkzeug.datastructures import MultiDict
import csv
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

#locals
import datenauswertung
import wiegand
import pigpio
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dein_geheimes_schlüssel'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nutzer.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=1)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Passwort des Systems
SYSTEM_PASSWORD_HASH = generate_password_hash("1234", method='pbkdf2:sha256')


# Benutzer-Model für Login (minimal, nur für Login-Verwaltung)
class User(UserMixin):
    id = 1  # Nur ein fester User ohne DB-Nutzung


@login_manager.user_loader
def load_user(user_id):
    if user_id == '1':
        return User()
    return None


authenticated = False

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if check_password_hash(SYSTEM_PASSWORD_HASH, password):
            user = User()
            login_user(user)
            return redirect(url_for('benutzer'))
        else:
            flash('Falsches Passwort, bitte erneut versuchen.')
    return render_template('login.html')

#Übersicht über Logdateien und kann dann auf Benutzerverwalten abspringen
@app.route("/benutzer")
@login_required
def benutzer():
    error = None
    with open("logdatei.txt", "r",encoding='windows-1252') as file:
        log_content = file.read()
    return render_template("benutzer.html", error=error, log_content=log_content)


@app.route("/benutzer/benutzerverwaltung", methods=['GET', 'POST'])
@login_required
def benutzerverwaltung():
    error = None  
    # Daten aus der CSV-Datei lesen
    with open("daten.csv", "r") as file:
        reader = csv.reader(file, delimiter=';')
        # Die erste Zeile enthält die Spaltennamen
        columns = next(reader)
        # Die restlichen Zeilen enthalten die Datensätze
        data = list(reader)

    
    #Wenn man einen Benutzer löscht wird dieser dann hier gelöscht weil er mittels get request übergeben wird
    row_id = request.args.get('rowId')
    delete = request.args.get('delete')
    if row_id is not None and delete == "True":
        row_id = int(row_id)
        datenauswertung.delete_user(row_id)
        # Umleitung zur gleichen URL und leere Query-Parameter
        return redirect(url_for('benutzerverwaltung', **remove_row_id(request.args)))
        
    #Wenn ein Benutzer bearbeitet wurde dann ist in der Querry rowID und username
    username = request.args.get('username')
    old_rowId = request.args.get('old_rowId')
    if username is not None:
        try:
            if old_rowId is not None:
                old_rowId = int(old_rowId)
            row_id = int(row_id)
            datenauswertung.delete_user(old_rowId) #löscht Benutzer mit rowId und fügt neuen wieder hinzu
            datenauswertung.add_user(row_id,username)
            # Umleitung zur gleichen URL und leere Query-Parameter
            return redirect(url_for('benutzerverwaltung', **remove_row_id(request.args)))
        except TypeError:
            return "Fehler, Eingabe konnte nicht gespeichert werden da die Chipnummer nur aus Zahlen bestehen muss"
        
    return render_template("benutzerverwaltung.html", error=error, columns=columns, data=data)

#entfernt die Querry die übergeben wird wenn ein Benutzer gelöscht wird
def remove_row_id(query_args):
    args_dict = query_args.to_dict()
    args_dict.pop('rowId', None)
    args_dict.pop('delete', None)
    args_dict.pop('username', None)
    args_dict.pop('old_rowId', None)
    return MultiDict(args_dict)

@app.route("/benutzer/benutzerverwaltung/loeschen")
@login_required
def loeschen():
    row_id = request.args.get('rowId')  # Holen Sie sich die übergebene Row-ID
    # Lesen Sie die Daten aus der "daten.csv" Datei und finden Sie die entsprechende Zeile
    with open("daten.csv", "r") as file:  # Öffnen Sie die Datei mit dem latin-1 Zeichensatz
        reader = csv.reader(file, delimiter=';')
        # Die erste Zeile enthält die Spaltennamen
        headers = next(reader)
        # Die restlichen Zeilen enthalten die Datensätze
        data = list(reader)
        print(data)
        # Vergleicht ob sich die ID in der Tabelle befindet
        for i in range(len(data)):
            if row_id in data[i]:
                print("gefunden")
                row = data[i]
                return render_template("loeschen.html", row=row, headers=headers, row_id=row_id)
    # Wenn die Row-ID nicht gefunden wurde, zeigen Sie eine entsprechende Meldung an
    return render_template("loeschen.html", row=None, headers=None, row_id=row_id)


@app.route("/benutzer/benutzerverwaltung/loeschen/bestaetigen", methods=['GET', 'POST'])
@login_required
def bestaetigen():
    row_id = request.args.get('rowId')  # Holen Sie sich die übergebene Row-ID
    return render_template("bestaetigen.html", row_id=row_id)


@app.route("/benutzer/benutzerverwaltung/bearbeiten")
@login_required
def bearbeiten():
    row_id = request.args.get('rowId')  # Holen Sie sich die übergebene Row-ID
    # Lesen Sie die Daten aus der "daten.csv" Datei und finden Sie die entsprechende Zeile
    with open("daten.csv", "r") as file:  # Öffnen Sie die Datei mit dem latin-1 Zeichensatz
        reader = csv.reader(file, delimiter=';')
        # Die erste Zeile enthält die Spaltennamen
        headers = next(reader)
        # Die restlichen Zeilen enthalten die Datensätze
        data = list(reader)
        print(data)
        # Vergleicht ob sich die ID in der Tabelle befindet
        for i in range(len(data)):
            if row_id in data[i]:
                print("gefunden")
                row = data[i]
                return render_template("bearbeiten.html", row=row, headers=headers, row_id=row_id)


@app.route("/benutzer/benutzerverwaltung/benutzer_hinzufuegen")
@login_required
def benutzer_hinzufuegen():
    readactivated = request.args.get('readactivated')
    if readactivated == 'True':
        #hier wird auf auf die Ausgabe des Wiegandcontrollers gewartet
        chipreaded = wiegand_add_user()
        readactivated = None
        #sobald eingabe erfolgt ist
        return render_template("benutzer_hinzufuegen.html", readactivated=readactivated, chipreaded=chipreaded)
    return render_template("benutzer_hinzufuegen.html", readactivated=readactivated)

    

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/download_daten')
@login_required
def download_daten():
    # Hier wird die Datei "daten.csv" zum Download bereitgestellt
    try:
        return send_file('daten.csv', as_attachment=True)
    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for('benutzerverwaltung'))

@app.route('/download_logdatei')
@login_required
def download_logdatei():
    # Hier wird die Datei "logdatei" zum Download bereitgestellt
    try:
        return send_file('longlogdatei.txt', as_attachment=True)
    except Exception as e:
        print(f"Error: {e}")
        return redirect(url_for('benutzerverwaltung'))
    

semaphore = threading.Semaphore(0)
# Variable zum Speichern des empfangenen Werts
received_value = None

def callback(bits, value):
    global received_value
    if bits == 26:
        received_value = value
        # Entsperre die Semaphore, um den Wert zugänglich zu machen
        semaphore.release()

def wiegand_add_user()->int:
    pi = pigpio.pi()
    global received_value
    w = wiegand.decoder(pi, 14, 15, callback)
    # Warten, bis der Wert empfangen wird
    semaphore.acquire()
    # Nachdem der Wert empfangen wurde, stoppe den Decoder
    w.cancel()
    # Gib den empfangenen Wert zurück
    print(received_value)
    return received_value

from multiprocessing import Process
def start_website(on_off):
    server = Process(target=app.run(debug=False, host='0.0.0.0'))
    if on_off:
        server.start()
    else:
        server.terminate()
    
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')



