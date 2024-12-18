# Installation

This script permit you to automatically send several commands in several switches. This README.md is an operating mode to install and use this script on Windows 10/11.

## Install Python3

First, install the latest version of the .exe from Windows Installer category on the website of [Python](https://www.python.org/downloads/windows/), for that follow this documentation : [Doc python](https://phoenixnap.com/kb/how-to-install-python-3-windows) 

## Install PIP

You have to go to a windows command prompt and to the location of the file get-pip.py. Now, you can run these commands : 

```pyhton
python get-pip.py
python.exe -m pip install --upgrade pip
pip install netmiko
```

To check if Netmiko is installed, run the following commands. This should give you the version of Netmiko installed :
```python
python
import netmiko
print(netmiko.__version__) 
```

# Use

## Add a switch or command with a file

To add a switch or command with a file, you can modify the .csv file. The first column is is the name or ip address of the switches, he second is for commands and the last one is for possible responses to commands. You can add a "#" to comment out a box that the script should not take into account. Example :

![Add switch/command](https://github.com/cbureau-gpsea/automatic_commands_switches/blob/main/img/with_file.png)

## Add a switch without file

To add a switch, you must change the field ***"ip"*** in switch list, by name or ip adress of your switch. You can add as many switches as you want.

![Add switch](https://github.com/cbureau-gpsea/automatic_commands_switches/blob/main/img/switch.png)

## Add a command without file

To add a command, you must change the field ***"command"*** by your command and the field ***"response"*** by the response your order could expect. If your command isn't waiting for a response, leave the field empty.

![Add command](https://github.com/cbureau-gpsea/automatic_commands_switches/blob/main/img/command.png)

## Launch script

To launch this script without file, execute this command :

```python
python command.py
```

With a file execute this command :

```python
python command.py [name_of_file].csv
```

# List of compatible switches

- Cisco Catalyst 3560
- Cisco Catalyst 3850
- Cisco Catalyst 9200L
- Cisco Catalyst 1000
- Cisco Business 250
- Cisco SG350XG
- Cisco Catalyst 2960
