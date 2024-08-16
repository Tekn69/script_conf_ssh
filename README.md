# Windows

Exécuter directement le script
```powershell
windows/python.exe script_conf_ssh.py
```

# Linux

Se déplacer dans le répertoire linux et télécharger miniconda à l'intérieur
```
cd linux/ && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ./miniconda.sh
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