# ADECalendar
Pour le faire fonctionner, il faut :
- un fichier nommé gm dans le dossier iMacros qui contient au moins les trois lignes suivantes (et éventuellement trois autres de même nature) 
    Ligne 1. user
    Ligne 2. mdp
    Ligne 3. nom dans ADE
- un fichier nommé UfrChoices.csv dans iMacros/Datasources contenant une liste des formations dans lesquelles on peut intervenir. Les lignes de cette liste débutant par # sont ignorées. L'exemple suivant permet de récupérer les emplois du temps à la FST et à l'ENSISA de l'enseignant référencé dans gm:
    FST 2016-2017
    #IUT Colmar 2015-2016
    #IUT Colmar 2016-2017
    #IUT Mulhouse 2016-2017
    ENSISA 2016-2017
    #FLSH 2016-2017
    #FMA 2016-2017
    #FSESJ 2016-2017
