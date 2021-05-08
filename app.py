
import base64
from io import BytesIO
import contextily
from flask import Flask, render_template, request, redirect, url_for, session,Response
import re
import pyodbc as py
import pandas as pd
import numpy as np
import geopandas
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from shapely.geometry import Point

  
  
app = Flask(__name__)

app.secret_key = 'your secret key'



#stringa di connessione con sql server tramite pyodbc
server = "213.140.22.237\SQLEXPRESS"
database = "zanella.luca"
username = "zanella.luca"
password = "xxx123##"

#connessione normale per far si che si possa connettere il server
conn = py.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password) 
@app.route("/")
#sulla pagina /login si fa metodo get post per passare le informazioni da html a python, in questo caso bisogna usare il post
@app.route('/login', methods =['GET', 'POST'])
#TODO: andreamo a fare il salvataggio su sql di quando l'utente si lgga
def login():
    #si inizializza un messaggio per poi andare a dire nell'if quando riuscito che il log è andato a buon fine
    msg = ''
    #se utilizziamo il post (e si utilizza quello per prendere informazioni) questo request form avrà sia username che password
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        #andiamo ad assegnare lo username e la password alle variabili interessate che poi andiamo a gestire
        username = request.form['username']
        password = request.form['password']
        #creaiamo un cursore che andrà a ascalare tutto quello che gli diciamo come un cursore vero
        cursor = conn.cursor()
        #query che dice username e la password assegnati prima andranni ad essere assegnati ai specifici campi username e password
        cursor.execute('SELECT * FROM accounts WHERE username = ? AND password = ?', (username, password, ))
        account = cursor.fetchone()
        if account:
            #se il login è riouscto 
            session['loggedin'] = True
            #se l'id matcha con la prima colonna che ho su sql questo è un array
            session['id'] = account[0]
            #stessa cosa con l'usernaname per il numero della colonna quindi bisogna fare un match tra quello scritto sull db e quello scritto adesso dall'utente nel login
            session['username'] = account[1]
            #se tutto va a buon fine il messaggio sarà quello che poi verrà ripreso su html tramite il render_template
            msg = 'Logged in successfully !'
            #per far vedere quale html voglio usare o voglio far vedere

           #si può iniziare con l'handling dei data frame

           
            #return render_template('index.html', msg = msg)
            return redirect(url_for("cookie"))

            

            
            
        else:
            #caso contrario messaggio normale di errore e passa anche questo per farlo vedere su html
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)

#pagina di logut che poi verrà messo dentro una navbar questa funzione per far si che ci si possa sloggare quando si vuole
#non che serva a molto anche perchè ti chiede sempre di loggarsi quando si entra


@app.route("/cookie")
def cookie():
    return render_template("cookie.html")

@app.route("/index",methods=["GET","POST"])
def index():
    #creazione della figura
    fig = Figure()
    ax = fig.add_subplot()

    #richiesta della tabella a sql server
    query_somm_vacc = 'SELECT * FROM dbo.puntiSomministrazioneVaccini'
    somm_vacc = pd.read_sql_query(query_somm_vacc,conn) 

    #richiesta del cookie creato in cookie.html
    coord = request.cookies.get('coord')
    lat = float(coord.split(":")[0])
    lon = float(coord.split(":")[1])

    #posizione serve per passare le coordinate a js per fa uscire il marker verde che saremmo il device
    posizione = [lat,lon]

    #creazione el punto dell'utente per calcolare i centri vaccinali in un raggio di 4 km
    punto_utente = Point([lat,lon][::-1])
    punto = geopandas.GeoSeries([punto_utente], crs='EPSG:4326').to_crs(epsg=3857)
    #creazione del buffer
    buffer = punto.buffer(4000)
    somm_vacc = geopandas.GeoDataFrame(somm_vacc,geometry=geopandas.points_from_xy(somm_vacc["lng"],somm_vacc["lat"]))
    somm_vacc.crs = 'epsg:4326'

    somm_vacc = somm_vacc.to_crs(epsg=3857)
    buffer = buffer.to_crs(epsg=3857)

    #i centri vaccinali che sono all'interno del buffer
    vacc = somm_vacc[somm_vacc.geometry.within(buffer.geometry.squeeze())]
    coordiante = np.array(vacc[['lat','lng','denominazione_struttura']])
    #print(coordiante)

    #creazione dell'array così che javascript possa capirlo senza che nessuno debba decodare niente
    result = ""
    for cord in coordiante:
        result += "[" + str(cord[1]) + "," + str(cord[0]) + ","  + "'"  + str(cord[2]) + "'" + "],"

#la lunghezza di result - l'ultimo carattere che è la virgola che non mi serve più le quadre è per l'array muldidimansionale
    result = "[" + result[0:len(result) -1] + "]"
    return render_template("index.html" , posizione = posizione, x = result)
    

#TODO:logout qui poi andremo a salvare quando è uscito dal sito 
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


#stesso metotdo usato prima per il login ma l'unico controllo è quello che colui che si registra non esisti già
@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    #qua prendo username password ed email per registrare vanno tutti nel requesto form
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        #poi vengono passati tutti nelle specifiche variabili
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        #si crea un cursore per scorrere come prima
        cursor = conn.cursor()
        #quan prendo l'username per fare un match che non esista già
        cursor.execute('SELECT * FROM accounts WHERE username = ?', (username, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
            #match per fa si che non entri nessuno script o cose strane
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
            #stessa cosa per username
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers !'
        elif not username or not password or not email:
            #nel caso sia vuoto
            msg = 'Please fill out the form !'
        else:
            #in caso vada tutto bene quello che mette l'utente si inseriscono dentro i campi username password ed email i valori messi dall'utente per registrarsi
            cursor.execute('INSERT INTO accounts (username,password,email) VALUES (?, ?, ?)', (username, password, email, ))
            #commito perchè se non sql viene bloccato dal programma e continua ad eseguire così come funziona github
            conn.commit()
            #messaggio di successo
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        #nel caso l'utente non abbia ancora riempito i form allora se provasse a loggarsi viene fuori messaggio di errore
        msg = 'Please fill out the form !'
        #qui faccio come prima per login.html ma con una pagina register
    return render_template('register.html', msg = msg)

if __name__ == '__main__':
   app.run(debug=True)
