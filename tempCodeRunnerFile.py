def file_exist():
    waiting = 2
    attemps = 3 
    for i in range(attemps):
        file_path = os.path.join(os.getcwd(), "d_order1")
        if os.path.isfile(file_path):
            print("Soubor d_order1 existuje.")
            return True
            
        else:
            print(f"Nepodařilo se najít soubor d_order1 na {i+1}. pokusu, zkouším to znovu za ",waiting," sekund")
            time.sleep(waiting)

    print("nepodařilo se najít soubor d_order1 po ",attemps," pokusech")
    return False