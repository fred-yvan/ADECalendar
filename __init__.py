# -*- coding: utf-8 -*-
import psutil
import time
import os
import icalendar
import googleCalendar
import smtplib
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from os.path import basename
from xvfbwrapper import Xvfb
from collections import namedtuple
import json
from datetime import datetime
import pytz
import sys
from enum import Enum


Vevent = namedtuple('Vevent', ['dtstart', 'dtend', 'description', 'summary',
                    'location', 'googlCalID'])


# Supprime tous les processes firefox
def killFireFox():
    for proc in psutil.process_iter():
        try:
            if proc.name() == "firefox-esr" or proc.name() == "firefox":
                proc.kill()
        except Exception:
            pass


def sendMail(subject, body=None, files=None):
    try:
        s = smtplib.SMTP("smtp.gmail.com", 587)
        s.ehlo()
        s.starttls()
        s.ehlo
        s.login(user, password)
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = user
        msg['Subject'] = subject
        if body is not None:
            msg.attach(MIMEText(body.encode('utf-8'), 'plain', 'utf-8'))
        for img in files or []:
            if os.path.isfile(img):
                with open(img, "rb") as fil:
                    part = MIMEApplication(
                        fil.read(),
                        Name=basename(img)
                    )
                part['Content-Disposition'] = \
                 'attachment;filename="%s"' % basename(img)
                msg.attach(part)
        s.sendmail(user, user, msg.as_string())
        s.quit()
    except Exception:
        sys.stderr.write("Error sending mail")


# On hérite simplement de l'encodeur de base pour faire son propre encodeur
class JSONEncoder(json.JSONEncoder):

    # Cette methode est appelee pour serialiser les objets en JSON
    def default(self, obj):
        # Si l'objet est de type datetime, on retourne une chaine formatee
        # representant l'instant de maniere classique
        # ex: "2014-03-09 19:51:32.7689"
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S.%f')
        return json.JSONEncoder.default(self, obj)


# On se fait des raccourcis pour loader et dumper le json
def json_dumps(data):
    return JSONEncoder().encode(data)


def saveCal(cal, fileName):
    f = open(fileName, "w")
    for i in range(len(cal)):
        tmpStr = json_dumps(cal[i].__dict__)
        if i is not 0:
            f.write("\n")
        f.write(tmpStr)
    f.close()


def loadCal(fileName):
    cal = []
    with open(fileName) as fp:
        for line in fp:
            tmp = json.loads(line)
            dts = datetime.strptime(tmp['dtstart'], '%Y-%m-%d %H:%M:%S.%f')
            dts = dts.replace(tzinfo=pytz.UTC)
            dte = datetime.strptime(tmp['dtend'], '%Y-%m-%d %H:%M:%S.%f')
            dte = dte.replace(tzinfo=pytz.UTC)
            desc = tmp['description']
            summ = tmp['summary']
            loca = tmp['location']
            goID = tmp['googlCalID'].encode('ascii', 'replace')
            e = Vevent(dtstart=dts,
                       dtend=dte,
                       description=desc,
                       summary=summ,
                       location=loca,
                       googlCalID=goID
                      )
            cal.append(e)
    return cal


# Ecrit le choix de l'UFR dans le fichier CurrentChoice.csv et retourne
# vrai si l'écriture s'est bien passé et faux dans le cas contraire ou
# si choix est vide ou est un commentaire, c'est-à-dire une chaîne qui
# commence par #
# Le fichier CurrrentChoice permet à iMacros d'ouvrir le calendrier de
# cette UFR.
def writeCurrentChoice(choix):
    choix = choix.strip()
    if choix == '' or choix.startswith('#'):
        return False
    else:
        try:
            if os.path.isfile(home + '/iMacros/Datasources/CurrentChoice.csv'):
                os.remove(home + '/iMacros/Datasources/CurrentChoice.csv')

            fchoix = open(home + '/iMacros/Datasources/CurrentChoice.csv', 'w')
            fchoix.write(choix)
            fchoix.close()
            return True
        except:
            return False


def getAbsoluteDirectoryDownload():
    if os.path.isdir(home + '/Téléchargements'):
        return home + '/Téléchargements/'
    else:
        return home + '/Downloads/'


def waitingUntilDownloadedOrCrasched(p, vdisplay, absoluteDirectoryDownload):
    c = 0
    fileList = []
    state = None
    while True:
        # ---------------------------------
        # Si Firefox a ete ferme, le script s'arrete aussi
        if p.status() == 'zombie':
            if vdisplay is not None:
                vdisplay.stop()
            return {"state": State.firefoxIsDead, "fileList": []}
        # Si le fichier ics a ete cree, on arrete la boucle
        if os.path.isfile(absoluteDirectoryDownload + 'ADECal.ics'):
            return {"state": State.calIsDownloaded, "fileList": []}
        # Fait une copie d'ecran
        fileName = "screenshot" + str(c) + ".png"
        fileList = fileList + [fileName]
        os.system("scrot " + fileName)
        time.sleep(10)
        c = c + 1
        if c > 30:
            return {"state": State.error, "fileList": fileList}


def main():
    # -----------------------
    # -- Le fichier
    choices = open(home + '/iMacros/Datasources/Choices.csv', 'r')

    absoluteDirectoryDownload = getAbsoluteDirectoryDownload()

    for choix in choices:

        if writeCurrentChoice(choix):

            # Arrete FireFox
            killFireFox()

            # Supprime le fichier contenant le calendrier
            if os.path.isfile(absoluteDirectoryDownload + 'ADECal.ics'):
                os.remove(absoluteDirectoryDownload + 'ADECal.ics')

            # Si le display n'existe pas, en creer un qui est virtuel'
            if 'DISPLAY' not in os.environ:
            # if not os.environ.has_key('DISPLAY'):
                vdisplay = Xvfb(width=970, height=490, colordepth=16)
                vdisplay.start()
            else:
                vdisplay = None
            # Execute la macro pour recuperer le calendrier
            p = psutil.Popen(['firefox', 'imacros://run/?m=ADECalendar.iim'])
            time.sleep(9)

            rep = waitingUntilDownloadedOrCrasched(p,
                                             vdisplay,
                                             absoluteDirectoryDownload)

            if rep["state"] == State.firefoxIsDead:
                continue

            time.sleep(5)

            # Arrete FireFox
            try:
                p.kill()
            except:
                pass

            if vdisplay is not None:
                vdisplay.stop()

            # Verifier si le fichier existe.
            # Si ce n'est pas le cas, envoyer un mail d'erreur de connexion
            # au serveur
            if not os.path.isfile(absoluteDirectoryDownload + 'ADECal.ics'):
                sendMail("Error", "ADECal.ics not generated", fileList)
                # Supprime les fichiers screenshot
                os.system("rm screenshot*.png")
                return

            # Supprime les fichiers screenshot
            os.system("rm screenshot*.png")

            # Load the icalendar file
            g = open(absoluteDirectoryDownload + 'ADECal.ics', 'rb')
            gcal = icalendar.Calendar.from_ical(g.read())
            g.close()

            newEvents = []
            for component in gcal.walk():
                if component.name == "VEVENT":
                    descrStr = component.get('description')
                    pos = descrStr.find('(')
                    if pos is not -1:
                        descrStr = descrStr[0:pos]
                    if descrStr[0] == "\n":
                        descrStr = descrStr[1:]
                    if descrStr[len(descrStr) - 1] == "\n":
                        descrStr = descrStr[0:len(descrStr) - 1]
                    e = Vevent(dtstart=component.get('dtstart').dt,
                               dtend=component.get('dtend').dt,
                               description=descrStr,
                               summary=component.get('summary'),
                               location=component.get('location'),
                               googlCalID='0'
                              )
                    newEvents.append(e)

            # Classer les evts par ordre croissant de dates
            newEvents.sort(key=lambda event: event.dtstart)

            """
            newEvents = loadCal('newADECal.txt')
            prevEvents = loadCal('prevADECal.txt')
            """

            # Ouvre le calendrier precedent
            modifEvt = []
            if os.path.isfile('prevADECal.txt'):
                prevEvents = loadCal('prevADECal.txt')
                # Trouve les cours a supprimer et ceux a rajouter
                evtToDel = []
                evtToAdd = []
                newEID = 0
                prevEID = 0
                while newEID < len(newEvents) and prevEID < len(prevEvents):
                    if newEvents[newEID].dtstart < prevEvents[prevEID].dtstart:
                        # Evenement a ajouter
                        e = newEvents[newEID]
                        evtToAdd.append(e)
                        newEID = newEID + 1
                    elif newEvents[newEID].dtstart > prevEvents[prevEID].dtstart:
                        # Evenement a supprimer
                        e = prevEvents[prevEID]
                        evtToDel.append(e)
                        prevEID = prevEID + 1
                    else:
                        if newEvents[newEID].dtend != prevEvents[prevEID]\
                           .dtend or\
                           newEvents[newEID].summary != prevEvents[prevEID]\
                           .summary or\
                           newEvents[newEID].location != prevEvents[prevEID]\
                           .location or\
                           newEvents[newEID].description != prevEvents[prevEID]\
                           .description:
                            e = prevEvents[prevEID]
                            evtToDel.append(e)
                            e = newEvents[newEID]
                            evtToAdd.append(e)
                        else:
                            e = prevEvents[prevEID]
                            modifEvt.append(e)
                        newEID = newEID + 1
                        prevEID = prevEID + 1
                while newEID < len(newEvents):
                    e = newEvents[newEID]
                    evtToAdd.append(e)
                    newEID = newEID + 1
                while prevEID < len(prevEvents):
                    e = prevEvents[prevEID]
                    evtToDel.append(e)
                    prevEID = prevEID + 1
            else:
                evtToAdd = newEvents
                evtToDel = []

            # Si il y a des cours a ajouter ou a supprimer
            if len(evtToAdd) != 0 or len(evtToDel) != 0:
                # Met a jour le calendrier Google
                googleCalendar.update(evtToAdd, evtToDel, modifEvt)
                modifEvt.sort(key=lambda event: event.dtstart)
                # Enregistre la nouvelle version du calendrier
                saveCal(modifEvt, 'prevADECal.txt')

                # Envoie un message pour indiquer les modifications faites
                tz = pytz.timezone('Europe/Paris')
                strAdded = '\nCours supprimes:\n'
                for i in range(len(evtToDel)):
                    dt1 = datetime.strftime(evtToDel[i].dtstart.astimezone(tz),
                        '%d/%m/%Y %H:%M')
                    dt2 = datetime.strftime(evtToDel[i].dtend.astimezone(tz),
                                            '-%H:%M')
                    strAdded = strAdded + dt1 + dt2 + ": " + \
                               evtToDel[i].summary + '\n'
                strAdded = strAdded + 'Cours ajoutes:\n'
                for i in range(len(evtToAdd)):
                    dt1 = datetime.strftime(evtToAdd[i].dtstart.astimezone(tz),
                                            '%d/%m/%Y %H:%M')
                    dt2 = datetime.strftime(evtToAdd[i].dtend.astimezone(tz),
                                            '-%H:%M')
                    strAdded = strAdded + dt1 + dt2 + ": " + \
                               evtToAdd[i].summary + '\n'
                sendMail('Update ADE: ' + str(len(evtToAdd)) + ' added and ' +
                         str(len(evtToDel)) + ' deleted', strAdded)
            # Envoie un message a Domesange pour indiquer
            # que le script s'est bien execute'
            sendMail('CMD', 'ADECalUpdtSucceed')
    choices.close()

if __name__ == '__main__':
    class State(Enum):
        firefoxIsDead = 1
        calIsDownloaded = 2
        error = 3

    home = os.getenv("HOME")
    infogm = open(home + '/iMacros/gm', 'r')
    user = infogm.readline()
    password = infogm.readline()
    main()
