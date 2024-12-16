from netmiko import ConnectHandler, NetmikoAuthenticationException
import re
import sys
import getpass

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

# Fonction pour tester le mot de passe administrateur des switchs
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

# Fonction pour entrer le mot de passe administrateur
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
                print("Erreur: Impossible de se connecter sur les switchs business avec le mot de passe actuel !")
            elif repsonse == 84:
                print("Erreur: Impossible de joindre ce switch !")
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

if __name__ == "__main__":
    sys.exit(main())
