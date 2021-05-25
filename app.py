
from flask import Flask,render_template, request, redirect, url_for, session
import re
import pandas as pd
import numpy as np
import geopandas
from shapely.geometry import Point
from datetime import datetime
import json
import pymssql as py



  
  
app = Flask(__name__)
app.secret_key = 'super secret key'
#app.secret_key = 'your secret key'

#stringa di connessione con sql server tramite pyodbc
server = "213.140.22.237\SQLEXPRESS"
database = "zanella.luca"
username = "zanella.luca"
password = "xxx123##"



#connessione normale per far si che si possa connettere il server
#conn = py.connect('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password) 
conn = py.connect(server,username,password,database)

@app.route("/")
#sulla pagina /login si fa metodo get post per passare le informazioni da html a python, in questo caso bisogna usare il post
@app.route('/login', methods =['GET', 'POST'])

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
        #-----
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password, ))
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


            global df_data_log
            df_data_log = datetime.now().strftime("%d/%m/%Y")
            df_data_log = datetime.strptime(df_data_log,"%d/%m/%Y")
            global df_time_iniziale
            df_time_iniziale = datetime.now().strftime("%H:%M:%S")
            
            #per far vedere quale html voglio usare o voglio far vedere ----
            cursor.execute('INSERT INTO dbo.prova_log (data,tempo_iniziale,ID_UTENTE) VALUES (%s,%s,%s)', (df_data_log,df_time_iniziale,session['id']))

            conn.commit()

            cursor.execute('SELECT TOP 1 * FROM dbo.prova_log WHERE ID_UTENTE = (%s) ORDER BY data DESC,tempo_iniziale DESC' , (session['id']))
            global id_prova_log
            id_prova_log = cursor.fetchone()
            print("id del log: " ,id_prova_log[0])



           #si può iniziare con l'handling dei data frame

           
            #return render_template('index.html', msg = msg)

            #questo permette di fare il redirect url_for ad una pagna https perchè di standard l'url for lo fa ad una pagina http
            return redirect(url_for("cookie",_external=True,_scheme='https'))
            #return redirect(url_for("cookie"))

        else:
            #caso contrario messaggio normale di errore e passa anche questo per farlo vedere su html solo se vogliamo mettere online il sito
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)

#pagina di logut che poi verrà messo dentro una navbar questa funzione per far si che ci si possa sloggare quando si vuole
#non che serva a molto anche perchè ti chiede sempre di loggarsi quando si entra

@app.route("/login_amministrator",methods=["GET","POST"])
def login_amministrator():
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
        cursor.execute('SELECT * FROM dbo.amministrator WHERE username = %s AND password = %s', (username, password, ))
        account = cursor.fetchone()
        if account:
            #se il login è riouscto 
            session['loggedin'] = True
            #se l'id matcha con la prima colonna che ho su sql questo è un array
            session['id'] = account[0]
            #stessa cosa con l'usernaname per il numero della colonna quindi bisogna fare un match tra quello scritto sull db e quello scritto adesso dall'utente nel login
            session['username'] = account[1]
            #se tutto va a buon fine il messaggio sarà quello che poi verrà ripreso su html tramite il render_template

            return redirect(url_for("graph_accounts_amministrator"))

        else:
            #caso contrario messaggio normale di errore e passa anche questo per farlo vedere su html solo se vogliamo mettere online il sito
            msg = 'Incorrect username / password !'
    return render_template('amministrator/login-amministrator.html', msg = msg)

@app.route("/graph_accounts_amministrator")
def graph_accounts_amministrator():
    cursor = conn.cursor()
    cursor.execute("""SELECT dbo.accounts.username, dbo.prova_log.data,dbo.prova_log.tempo_iniziale,dbo.prova_log.tempo_finale,dbo.prova_log.lat_utente,dbo.prova_log.lon_utente,dbo.ProvapuntiSomministrazioneVaccini.denominazione_struttura,dbo.ProvapuntiSomministrazioneVaccini.nome_area as area_punto_vacc
FROM dbo.accounts
INNER JOIN dbo.prova_log ON dbo.accounts.id = dbo.prova_log.ID_UTENTE
INNER JOIN dbo.Select_utente ON dbo.prova_log.ID = dbo.Select_utente.ID_LOG
INNER JOIN dbo.ProvapuntiSomministrazioneVaccini ON dbo.Select_utente.ID_PUNTO_VACCINALE = dbo.ProvapuntiSomministrazioneVaccini.Column_1
""")
    data = cursor.fetchall()

    return render_template("amministrator/accounts.html", data = data)

@app.route("/cookie")
def cookie():
    return render_template("cookie.html")

@app.route("/index",methods=["GET","POST"])
def index():

   # try:
        cursor = conn.cursor()
        

        #richiesta della tabella a sql server
        query_somm_vacc = 'SELECT * FROM dbo.ProvapuntiSomministrazioneVaccini'
        somm_vacc = pd.read_sql_query(query_somm_vacc,conn) 

        #richiesta del cookie creato in cookie.html
        coord = request.cookies.get('coord')
        lat = float(coord.split(":")[0])
        lon = float(coord.split(":")[1])

        print(lat,lon)


        cursor.execute('UPDATE dbo.prova_log  SET lat_utente = (%s),lon_utente = (%s) WHERE ID = (%s)',(lat,lon,id_prova_log[0]))
        conn.commit()





        #posizione serve per passare le coordinate a js per fa uscire il marker verde che saremmo il device
        posizione = [lat,lon]

        #creazione el punto dell'utente per calcolare i centri vaccinali in un raggio di 4 km
        punto_utente = Point([lat,lon][::-1])
        punto = geopandas.GeoSeries([punto_utente], crs='EPSG:4326').to_crs(epsg=3857)
        #creazione del buffer
        dimensione = 4000
        buffer = punto.buffer(dimensione)
        somm_vacc = geopandas.GeoDataFrame(somm_vacc,geometry=geopandas.points_from_xy(somm_vacc["lng"],somm_vacc["lat"]),crs=4326)
        #somm_vacc.crs = 'epsg:4326'

        somm_vacc = somm_vacc.to_crs(epsg=3857)
        buffer = buffer.to_crs(epsg=3857)

        #i centri vaccinali che sono all'interno del buffer
        vacc = somm_vacc[somm_vacc.geometry.within(buffer.geometry.squeeze())]
        coordiante = np.array(vacc[['lat','lng','denominazione_struttura']])
        #print(coordiante)

        #creazione dell'array così che javascript possa capirlo senza che nessuno debba decodare niente
        result = ""
        for cord in coordiante:
            result += "[" + str(cord[1]) + "," + str(cord[0]) + ","  + '"'  + str(cord[2]) + '"' + "],"

    #la lunghezza di result - l'ultimo carattere che è la virgola che non mi serve più le quadre è per l'array muldidimansionale
        result = "[" + result[0:len(result) -1] + "]"


        information = request.data.decode('utf-8')
        #print("*" + information + "*")

        if information != "":
            
            
            information = information
            information = json.loads(information)
            lat,lon = information['lat'],information['lng'] 
            #print(lat,lon)
            cursor.execute('SELECT * FROM dbo.ProvapuntiSomministrazioneVaccini WHERE lat = (%s) AND lng = (%s) ',(lat,lon))
            id_punto = cursor.fetchone()
            #id_punto = int(id_punto)
            cursor.execute('INSERT INTO dbo.Select_utente (ID_LOG,ID_PUNTO_VACCINALE) VALUES (%s,%s) ',(int(id_prova_log[0]),int(id_punto[0])))
            conn.commit()
            print("riuscita")

        


        return render_template("index.html" , posizione = posizione, x = result,dimensione = dimensione)

    #except:

     #   return redirect(url_for("login"))

@app.route('/logout')
def logout():
    cursor = conn.cursor()
    df_tempo_finale = datetime.now().strftime("%H:%M:%S")
    cursor.execute('UPDATE dbo.prova_log  SET tempo_finale = (%s) WHERE ID_UTENTE = (%s) AND data = (%s) AND tempo_iniziale = (%s)',(df_tempo_finale,session['id'],df_data_log,df_time_iniziale))
    conn.commit()



    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login',_external=True,_scheme='https'))
    #return redirect(url_for('login'))
    

@app.route("/graph")
def graph():

    query_graph = "SELECT * FROM dbo.ProvapuntiSomministrazioneVaccini"
    df_graph = pd.read_sql(query_graph,conn)
    df_graph = df_graph.groupby("area").count()["Column_1"].reset_index(name="num_vacc")
    df_graph = np.array(df_graph[['area','num_vacc']])

    labels = [row[0] for row in df_graph]
    values = [row[1] for row in df_graph]

    #vaccinazioni tra maschi e femmine in italia
    csv_somm_vacc = pd.read_csv("https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/somministrazioni-vaccini-latest.csv")
    somm_vacc = csv_somm_vacc.groupby("area").sum()[['sesso_maschile','sesso_femminile']].reset_index()
    somm_vacc = np.array(somm_vacc[['area','sesso_maschile','sesso_femminile']])

    maschi = [row[1] for row in somm_vacc]
    femmine = [row[2] for row in somm_vacc]
    area = [row[0] for row in somm_vacc]

    #pie per vedere quante dosi

    df_somm_vacc = csv_somm_vacc.groupby('fornitore').sum()[['sesso_maschile','sesso_femminile']].reset_index()
    df_somm_vacc['tot'] = (df_somm_vacc['sesso_maschile'] + df_somm_vacc['sesso_femminile'])
    df_somm_vacc = np.array(df_somm_vacc[['fornitore','tot']])

    fornitore = [row[0] for row in df_somm_vacc]
    totale_fornitore = [row[1] for row in df_somm_vacc]

    dosi = pd.read_csv("https://raw.githubusercontent.com/italia/covid19-opendata-vaccini/master/dati/vaccini-summary-latest.csv")
    dosi['da_utilizzare'] = dosi['dosi_consegnate'] - dosi['dosi_somministrate']
    dosi = np.array(dosi[['area','dosi_somministrate','da_utilizzare']])

    area_dosi = [row[0] for row in dosi]
    dosi_somministrate = [row[1] for row in dosi]
    da_utilizzare = [row[2] for row in dosi]

    return render_template("graph.html", values=values, labels = labels, maschi = maschi,femmine = femmine, area = area, fornitore = fornitore, totale_fornitore = totale_fornitore,area_dosi = area_dosi, dosi_somministrate = dosi_somministrate,da_utilizzare = da_utilizzare)

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
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username, ))
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
            cursor.execute('INSERT INTO accounts (username,password,email) VALUES (%s, %s, %s)', (username, password, email, ))
            #commito perchè se non sql viene bloccato dal programma e continua ad eseguire così come funziona github
            conn.commit()
            #messaggio di successo
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        #nel caso l'utente non abbia ancora riempito i form allora se provasse a loggarsi viene fuori messaggio di errore
        msg = 'Please fill out the form !'
        #qui faccio come prima per login.html ma con una pagina register
    return render_template('register.html', msg = msg)



