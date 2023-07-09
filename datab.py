import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import time
import config

def create_conn(max_attempts=10, sleep_time=60):
    attempts = 0
    conn = None
    while attempts < max_attempts:
        try:
            conn = psycopg2.connect(**config.db_config)
            print("Úspěšně připojeno k databázi")
            break
        except psycopg2.OperationalError as e:
            print("Chyba při připojení k databázi: ", e)
            attempts += 1
            print("Zkouším znovu za {} sekund...".format(sleep_time))
            time.sleep(sleep_time)
    if conn is None:
        print("Nepodařilo se připojit k databázi po {} pokusech".format(max_attempts))
    return conn

def database_exists(cur, dbname):
    cur.execute("""
        SELECT COUNT(*) 
        FROM pg_catalog.pg_database 
        WHERE datname = %s
    """, (dbname.lower(),))  
    return cur.fetchone()[0] == 1

def table_exists(cur, tablename):
    cur.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_name = %s
    """, (tablename.lower(),)) 
    return cur.fetchone()[0] == 1



conn = create_conn()
if conn is None:
    exit(1) # ukončí skript s chybovým kódem, pokud se nepodaří připojit k databázi

conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

# Připojení k nově vytvořené databázi
conn = psycopg2.connect(**config.db_config)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

# Kontrola existence tabulky items a pokus o její vytvoření
print("testuji zda existuje tabulka items")
try:
    if not table_exists(cur, 'items'):
        cur.execute(
            """
            CREATE TABLE items(
                id SERIAL PRIMARY KEY,
                title VARCHAR(100),
                image_url VARCHAR(250)
            );
            """
        )
        print("Tabulka 'items' vytvořena.")
    else:
        print("Tabulka 'items' již existuje.")
except psycopg2.errors.DuplicateTable:
    print("Tabulka 'items' již existuje.")

# uložení změn a ukončení spojení
conn.commit()
conn.close()
print("Spojení s databází ukončeno.")
file_path = "/data/d_order1"
with open(file_path, 'w') as f:
    print(f"Soubor {file_path} byl vytvořen.")
    pass