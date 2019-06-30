Procédure de pré-création de comptes sur Polytechnique.org en lien avec l'AX et l'École polytechnique
=====================================================================================================

Voici comment devrait se passer l'import d'une promotion d'anciens élèves dans le système d'information de Polytechnique.org, afin que les anciens élèves puissent s'inscrire sur Polytechnique.org et accéder aux services de la communauté polytechnicienne.

* L'AX :

  - récupère la liste de la nouvelle promotion sur le guichet de la DSI de l'École polytechnique (sauf cas particuliers des docteurs, récupérés directement) ;
  - définit des matricules AX ;
  - envoie le fichier résultant à Polytechnique.org (au format CSV, LibreOffice ou Excel) ;
  - supprime le mail envoyé du dossier "messages envoyés" après son envoi.

* Polytechnique.org :

  - récupère la liste de la nouvelle promotion sur le guichet de la DSI de l'École polytechnique ;
  - ajoute dans cette liste les matricules AX (script ``01_parse_school_csv.py``) ;
  - crée les comptes sur https://www.polytechnique.org (Menu: Administration, Gestion des comptes, Ajout d'un ensemble d'utilisateurs, une promotion) ;
  - supprime le mail envoyé par l'AX de sa boîte de réception.

Ceci permet aux étudiants de s'inscrire sur Polytechnique.org et d'accéder au SSO (https://auth.polytechnique.org).

* Polytechnique.org :

  - exporte les logins X.org (``prenom.nom.promo``) et les adresses emails (``@polytechnique.org`` pour les étudiants du cycle ingénieur, ``@alumi.polytechnique.org`` pour les autres) de sa base de données (script ``02_export_platal_profiles_to_json.py`` à exécuter dans l'environnement du SSO) ;
  - ajoute ces logins X.org à la liste de promotion (script ``03_merge_with_school_csv.py`` à exécuter avec le fichier de l'École et la sortie du script précédent, ``exported_for_ax.json``, afin de produire un fichier Excel, ``export_pour_ax.xlsx``) ;
  - dépose le fichier Excel sur un serveur avec un nom qui comporte une composante aléatoire ;
  - envoie l'URL du fichier déposé à l'AX (destinataires : Aurélie Lafaurie et Anne Maginot).

* L'AX :

  - importe ce fichier sur son site (https://ax.polytechnique.org), ce qui permet aux étudiants d'y accéder en se connectant par le SSO ;
  - prévient Polytechnique.org et la DSI de l'École polytechnique que les comptes ont été importés.

Ceci permet de répondre aux étudiants dont le compte n'aurait pas été créé que cela est très probablement lié à la non-acceptation de la transmission de leurs données personnelles sur le site mis en place par la DSI de l'X et qu'il faut qu'ils cochent une case sur celui-ci (l'URL de ce site a changé au fil des annnées et la référence doit être maintenue sur https://auth.polytechnique.org/faq).

* Polytechnique.org :

  - supprime le fichier Excel qui a été déposé sur un serveur, une fois que l'AX l'a utilisé (afin d'éviter que des informations à caractère personnel traînent sur Internet ou dans des boîtes mail).
