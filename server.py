import psycopg2
from flask import Flask, render_template
import time
import config
import os

app = Flask(__name__)
@app.route('/')

def home():
    conn = try_to_connect_to_database()
    if conn:
        table_exist = check_existence_of_table(conn)
        if table_exist == True:
            items = load_data(conn)
            if items:
                return render_template('index.html', items=items)
            else:
                return "Databáze existuje, relace exisstuje ale neobsahuje data"
        else:
           return "Databáze existuje ale neobsahuje relaci"         
    else: 
        return "Databáze neexistuje"

# Try to connect to the database
def try_to_connect_to_database():
    sleep_time = 60
    max_attempts = 20
    attempts = 0
    while attempts < max_attempts:
        try:
            print("Pokouším se připojit k databázi na" ,attempts," pokus")
            conn = psycopg2.connect(**config.db_config)
            print("Úspěšně připojeno k databázi.")
            return conn
            # break
        except psycopg2.OperationalError as e:
            print(f"Nepodařilo se připojit k databázi. Chyba: {str(e)}")
            attempts += 1
            print(f"Zkouším znovu za {sleep_time} sekund...")
            time.sleep(sleep_time)
            
    print("k databázi se nepodařilo připojit po ",attempts," databáze neexistuje nebo jsou špatně přihlašovací udaje")
    conn = None
    return conn

# Check if table exists in the database
def check_existence_of_table(conn):
    sleep_time = 60
    max_attempts = 10
    attempts = 0
    while attempts < max_attempts:
        try:
            cur = conn.cursor()
            cur.execute("SELECT to_regclass('public.items')") #muže dojít k vyjímce 
            table_exists = cur.fetchone()[0]
            if table_exists is not None: #muže dojít k vyjímce 
                print("v databázi existuje tabulka items")
                return True
            else:
                raise psycopg2.DatabaseError("Tabulka 'items' nebyla nalezena.")
        except (psycopg2.DatabaseError) as e:
            print(f"Nepodařilo se zkontrolovat existenci tabulky. Chyba: {str(e)}")
            attempts += 1
            print(f"Zkouším znovu za {sleep_time} sekund...")
            time.sleep(sleep_time)
    
    print("bylo provedeno ",attempts," pokusu o nalezeni tabulky, tabulka bohužel není v databázi")
    try:
        conn.close()
        print("Spojení s databázi bylo úspěšně ukončeno.")
    except psycopg2.OperationalError as e:
        print(f"Nepodařilo se ukončit spojení s databází. Chyba: {str(e)}")

    return False

# try to load data
def load_data(conn):
    sleep_time = 60
    max_attempts = 10
    attempts = 0
    while attempts < max_attempts:
        try:
            cur = conn.cursor()
            query = "SELECT title, image_url FROM items"
            print(f"Provádím dotaz: {query}")
            cur.execute(query)
            items = cur.fetchall()
            print("Výsledky dotazu:")
            for item in items:
                print(item)
            try:
                conn.close()
                print("Spojení s databázi bylo úspěšně ukončeno.")
            except psycopg2.OperationalError as e:
                print(f"Nepodařilo se ukončit spojení s databází. Chyba: {str(e)}")
            return items
        
        except psycopg2.DatabaseError as error:
            print(f"Chyba při získávání dat z databáze: {error}")
            attempts += 1
            print(f"Zkouším znovu za {sleep_time} sekund...")
            time.sleep(sleep_time)

    print("bylo provedeno ",attempts," pokusu o načtení data, data bohužel nejsou v databázi")
    return None

def file_exist():
    waiting = 60
    attemps = 15
    for i in range(attemps):
        file_path = "/data/d_order2"
        if os.path.isfile(file_path):
            print("Soubor d_order2 existuje.")
            return True
            
        else:
            print(f"Nepodařilo se najít soubor d_order2 na {i+1}. pokusu, zkouším to znovu za ",waiting," sekund")
            time.sleep(waiting)

    print("nepodařilo se najít soubor d_order2 po ",attemps," pokusech")
    return False

if file_exist() == True:
    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=8080, debug=True) 
else:
    print("Script spider.py neproběhl uspěšně, soubor d_order2 nebyl nalezen")
