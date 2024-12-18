from netmiko import ConnectHandler, NetmikoAuthenticationException
import re
import sys
import getpass
import os
import csv

# Liste des switchs avec leurs noms
switch_list = [
    {"ip": "NAME OR IP OF SWITCH 1", "device_type": "cisco_ios", "username": "", "password": ""},
    {"ip": "NAME OR IP OF SWITCH 2", "device_type": "cisco_ios", "username": "", "password": ""},
]

# Commandes à lancer sur les switchs
commands = [
    {"command": "COMMAND 1", "response": ""},
    {"command": "COMMAND 2", "response": "YES"},
]

# Fonction pour envoyer les commandes sur le switch
def command_switch(connection, model):
    global output
    try:
        for command in commands:
            if command['response'] != "":
                if command['command'] == "write memory":
                    if model == "CBS250" or model == "SG350XG":
                        output_first = connection.send_command_timing(command['command'])
                        output = re.sub(r".\[\d+m|.\[D|.\[K|.\[1m|.\[0m", "", output_first)
                        print(f"{output}")
                        output_bad = connection.send_command_timing(command['response'])
                    else:
                        output_bad = connection.send_command_timing(command['command'])
                else:
                    output_first = connection.send_command_timing(command['command'])
                    output = re.sub(r".\[\d+m|.\[D|.\[K|.\[1m|.\[0m", "", output_first)
                    print(f"{output}")
                    if command['command'] == "reload":
                        output_bad = connection.send_command_timing(command['response'])
            else:
                if command['command'] == "show ip int brief" or command['command'] == "show ip int":
                    if model == "CBS250" or model == "SG350XG":
                        output_bad = connection.send_command_timing("show ip int")
                    else:
                        output_bad = connection.send_command_timing("show ip int brief")
                else:
                    output_bad = connection.send_command_timing(command['command'])
            output = re.sub(r".\[\d+m|.\[D|.\[K|.\[1m|.\[0m", "", output_bad)
            print(f"{output}")
            print(f"___________________________________________________________________________________________________________________________________________")
            if model != "CBS250" and model != "SG350XG":
                    print(f"")
    except Exception as e:
        if command['command'] == "reload":
            print(f"___________________________________________________________________________________________________________________________________________")
            if output == "Reload command is being issued on Active unit, this will reload the whole stack\nProceed with reload? [confirm]" or output == "Proceed with reload? [confirm]" or output == "\nThis command will reset the whole system and disconnect your current session. Do you want to continue ? (Y/N)[N] ":
                print(f"\nLe switch est éteint !\n")
            else:
                print(f"\nLe switch est sûrement éteint !\n")
        else:
            print(f"Erreur sur la commande {command['command']}: {e}")
    return

# Fonction pour parser et récupérer le modèle du switch
def parse_model(output):
    pattern = re.compile(r'NAME: "(Switch 1|1)"', re.IGNORECASE)
    lines = output.strip().split("\n")
    matching_blocks = []
    
    for line in lines:
        if pattern.search(line):
            matching_blocks.append(line)
            for block in matching_blocks:
                descr_match = re.search(r'DESCR: "(.*?)"', block)
                if descr_match:
                    descr_value = descr_match.group(1)
                    descr_list = descr_value.split('-')
                    if descr_list[0] == "WS":
                        model = descr_list[1]
                    else:
                        model = descr_list[0]
                    return model
    return None

# Fonction pour se connecter sur chaque switch
def config_switch(switch):
    try:
        connection = ConnectHandler(**switch)
        connection.enable()
        print(f"\nConnexion sur {switch['ip']} réussie !")

        # Récupère le modèle du switch
        output_model = connection.send_command_timing("show inventory")
        model = parse_model(output_model)
        if model == None:
            print(f"Erreur: Impossible de trouver le modèle du switch {switch['ip']}")
            return
        else:
            print(f"Modèle du switch: {model}")
            if model != "CBS250" and model != "SG350XG":
                print(f"")

        # Lance les commandes sur le switch
        if model == "CBS250" or model == "SG350XG":
            connection.send_command_timing("terminal datadump")
        else:
            connection.send_command_timing("terminal length 0")
        command_switch(connection, model)
        if model == "CBS250" or model == "SG350XG":
            connection.send_command_timing("terminal no datadump")

        if model == "CBS250" or model == "SG350XG":
            print(f"")
        connection.disconnect()  
    except NetmikoAuthenticationException as e:
        print(f"Erreur: Impossible de se connecter sur {switch['ip']} avec le mot de passe actuel !")
    except Exception as e:
        if output == "Y\nShutting down ...\n":
            print(f"\nLe switch est éteint !\n")
        else:
            print(f"Erreur sur {switch['ip']}: {e}")
        return

# Fonction pour tester le mot de passe sur les switchs
def test_password(switch, user, password):
    switch['username'] = user
    switch['password'] = password
    try:
        connect = ConnectHandler(**switch)
        connect.enable()
        connect.disconnect()
        return True
    except NetmikoAuthenticationException as e:
        return False
    except Exception as e:
        return 84

# Fonction pour entrer le mot de passe
def enter_password():
    global password
    global user

    while True:
        user = input("Entrez le nom votre nom d'utilisateur: ")
        password =  getpass.getpass("Entrez votre mot de passe: ")

        if password == "exit" or user == "exit":
            exit(1)
        elif password == "" or user == "":
            print("\nErreur: Le mot de passe ou le nom d'utilisateur ne peut pas être vide !\n")
        elif password != "" and user != "":
            repsonse = test_password(switch_list[0], user, password)

            if repsonse == False:
                print("Erreur: Impossible de se connecter sur les switchs avec ces identifiants !")
            elif repsonse == 84:
                print(f"Erreur: Impossible de joindre le switch {switch_list[0]['ip']}, pour tester le mot de passe !")
                user = None
                password = None
                break
            elif repsonse == True:
                for switch_pwd in switch_list:
                    switch_pwd['username'] = user
                    switch_pwd['password'] = password
                break

# Exécuter la configuration sur tous les switchs
def main():
    enter_password()
    if user == None or password == None:
        exit(1)
    for switch in switch_list:
        config_switch(switch)

# Fonction pour supprimer les espaces, tabulations, sauts de ligne et caractères spéciaux
def remove_whitespace(text):
    return text.replace(" ", "").replace("\t", "").replace("\n", "").replace("\xa0", "").replace("\u2007", "").replace("\u202F", "")

# Fonction pour supprimer les cases vides
def remove_empty_rows(rows):
    return [row for row in rows if any(row[1:])]

# Fonction pour détecter le délimiteur du fichier CSV
def detect_delimiter(file_path):
    with open(file_path, 'r') as file:
        sample = file.read(1024)
        delimiters = [',', ';', '\t']
        delimiter_counts = {delimiter: sample.count(delimiter) for delimiter in delimiters}
        detected_delimiter = max(delimiter_counts, key=delimiter_counts.get)
        return detected_delimiter

# Fonction pour parser le fichier CSV
def parse(name_file):
    switch_list = []
    commands = []
    delimiter = detect_delimiter(name_file)

    try:
        if not os.path.isfile(name_file):
            raise FileNotFoundError(f"Le fichier {name_file} n'existe pas.")
        with open(name_file, 'r') as file:
            reader = csv.reader(file, delimiter=delimiter)
            rows = list(reader)
            rows = remove_empty_rows(rows)
            for row in rows:
                if len(row) > 0 and row[0]:
                    if row[0] != "" and row[0][0] != "#":
                        row[0] = remove_whitespace(row[0])
                        switch_list.append({"ip": row[0], "device_type": "cisco_ios", "username": "", "password": ""})
                if len(row) > 1 and row[1]:
                    if row[1] != "" and row[1][0] != "#":
                        if len(row) > 2 and row[2]:
                            if row[2] != "" and row[2][0] != "#":
                                commands.append({"command": row[1], "response": row[2]})
                            else:
                                commands.append({"command": row[1], "response": ""})
                        else:
                            commands.append({"command": row[1], "response": ""})
        main()
    except FileNotFoundError as e:
        print(e)
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"Une erreur est survenue lors de la lecture de votre fichier: {e}")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        sys.exit(parse(sys.argv[1]))
    elif len(sys.argv) == 1:
        sys.exit(main())
    else:
        print("Erreur: Trop d'arguments !")
        exit(1)
