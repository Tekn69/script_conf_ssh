# Windows

Exécuter directement le script dans powershell
```powershell
windows/python.exe script_conf_ssh.py
```

# Linux

Créer le répertoire linux, se déplacer dedans et télécharger miniconda à l'intérieur
```
mkdir linux && cd linux/ && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ./miniconda.sh
```

Installer miniconda dans le répertoire courant
```
bash miniconda.sh -b -p ./miniconda
```

Activer le venv miniconda
```
source miniconda/bin/activate
```

Exécuter le script
```
cd .. && python script_conf_ssh.py
```