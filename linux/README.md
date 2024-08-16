Miniconda_3.12.4 amd64 :
https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

Télécharger miniconda dans le répertoire courant
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ./miniconda.sh
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