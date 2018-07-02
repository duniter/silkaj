En résumé :

1. Créer un compte sur pypi / pypi de test
2. Génrérer des paquets wheel (un source, un binaire).
3. Envoyer les paquets sur pypi

# Créer un compte sur pypi

De test : https://test.pypi.org/account/register/

De production : https://pypi.org/account/register/

Ça permet de gérer les versions et les projets (notamment ajouter des collaborateurs qui pourront aussi faire des livraisons).

# Générer les paquets

D'abord il faut installer/mettre à jour `setuptools` et `wheels`

```bash
pip install -U setuptools wheel twine
```

Ensuite créer les paquets source et binaire dans le dossier "dist/" :

```bash
$ python3 setup.py sdist bdist_wheel
$ ls dist/
silkaj-0.6.0-py3-none-any.whl  silkaj-0.6.0.tar.gz
```

# Pousser les paquets sur pypi

Pour ne pas taper son password à chaque fois, on peut utiliser ça : https://github.com/pypa/twine#keyring-support

## Pousser sur l'environnement de test

Pour pousser la version $VERSION

```bash
twine upload --repository-url https://test.pypi.org/legacy/ dist/silkaj-$VERSION*
```

On peut voir le paquet ici : https://test.pypi.org/project/silkaj/


Pout installer le paquet depuis le dépôt de test sur un venv tout neuf :

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.python.org/simple/ silkaj
```

Le `--extra-index-url` sert à ajouter les paquets officiels, sinon il y aura un problème avec les dépendances absentes de l'environnement de test.

## Pousser sur l'environnement de test

Juste faire : `twine upload dist/silkaj-$VERSION*`

Pour installer le paquet dans un environnement tout propre :

```bash
pip install silkaj
```
