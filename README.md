Tapo is a python utility used via terminal to control power on tapo p300s smart Wi-Fi Power Strips
# Usage
The tapo APIs may be used via the tapo_control.py script. 
First clone this repository.
Then set the environment with the following commands:

```bash
echo export TAPO_PATH="/path/to/tapo/folder" >> ~/.bashrc

echo export TAPO_USERNAME="your_username" >> ~/.bashrc

echo export TAPO_PASSWORD="your_password" >> ~/.bashrc

echo export TAPO_P300_IPS="your_P300_IPs_separated_by_comma" >> ~/.bashrc

alias tapo="python3 $TAPO_PATH/tapo_control.py"

source ~/.bashrc
```
Then you have to install the tapo APIs with:

```bash
pip install tapo
```

Then you can simply type:

```bash
tapo -h
```
To have an help:
```
usage: tapo_control.py [-h] [-l] [-a NEW_IP] [-r OLD_IP] [child_nickname] [{on,off,reset}]

Control multiple Tapo P300 strips by nickname, list them, add IPs, or remove IPs from .bashrc.

positional arguments:
  child_nickname        Nickname of the child device (e.g. 'kriakv260').
  {on,off,reset}        Desired action: 'on', 'off', or 'reset' (force off->on).

options:
  -h, --help            show this help message and exit
  -l, --list            List all child devices across all configured Tapo P300 IPs and exit.
  -a NEW_IP, --add NEW_IP
                        Add a new IP to the TAPO_P300_IPS in /home/test/.bashrc and /root/.bashrc, then exit.
  -r OLD_IP, --remove OLD_IP
                        Remove an IP from TAPO_P300_IPS in /home/test/.bashrc and /root/.bashrc, then exit.
```
