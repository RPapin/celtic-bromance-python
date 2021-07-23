import json
import random
from os import listdir
from os.path import isfile, join
import subprocess
import os
from shutil import copyfile
import re
from datetime import date
from typing import final
import psutil 
import time
import infoApi as Info
from datetime import datetime

today = date.today()
accServerPath = "D:/Steam/steamapps/common/Assetto Corsa Competizione Dedicated Server/server/"
accServerPathCfg = accServerPath + "cfg/"
accServerPathResult = accServerPath + "results/"
dataPath = "Data/"
templatePath = "Template/"
savesPath = "saves/"
# Static cfg files, just need to put in the server folder
configFiles=["assistRules.json", "configuration.json", "settings.json"] 
ballastInGameLimit = 30
server = None

def init():
    with open(dataPath + 'cars.json') as json_file:
        carsData = json.load(json_file)
        json_file.close()
    with open(dataPath + 'tracks.json') as json_file:
        trackData = json.load(json_file)
        json_file.close()
    with open(dataPath + 'weatherConfiguration.json') as json_file:
        weatherData = json.load(json_file)
        json_file.close()


    return carsData, trackData, weatherData


def makeEventConfig(trackData, weatherData) :
    """ Create event and assist file from template"""
    with open(templatePath + 'event.json') as json_file1:
        templateEvent = json.load(json_file1)
        json_file1.close()
    eventInfo = {}
    # Choose track
    trackList = []
    for track in trackData :
        if trackData[track]["available"]:
            trackList.append(track)
    listTrack = random.choice(trackList)
    finalTrack = random.choice(trackData[listTrack]["tracks"])
    templateEvent["track"] = finalTrack
    eventInfo["track"] = finalTrack
    
    # Choose weather
    templateEvent["ambientTemp"] = random.randint(weatherData['ambientTemp']["min"], weatherData['ambientTemp']["max"])
    templateEvent["cloudLevel"] = round(random.uniform(weatherData['cloudLevel']["min"], weatherData['cloudLevel']["max"]), 1)
    #Choose rain level, 0.0 (dry) has 5x more chance to get
    for i in range(weatherData['rollNumber']):
        rain = round(random.uniform(weatherData['rain']["min"], weatherData['rain']["max"]), 1)
        if rain == 0 :
            break
    templateEvent["rain"] = rain
    templateEvent["weatherRandomness"] = random.randint(weatherData['weatherRandomness']["min"], weatherData['weatherRandomness']["max"])
    eventInfo.update({
        "Ambient temperature": templateEvent["ambientTemp"],
        "Cloud level": templateEvent["cloudLevel"],
        "Rain": templateEvent["rain"],
        "Weather randomness": templateEvent["weatherRandomness"]
    })

    # Choose daytime
    daytime = random.randint(0,23)
    timeMultipler = random.randint(0,24)
    templateEvent["sessions"][0]["hourOfDay"] = templateEvent["sessions"][1]["hourOfDay"] = daytime
    templateEvent["sessions"][0]["timeMultiplier"] = templateEvent["sessions"][1]["timeMultiplier"] = timeMultipler
    eventInfo.update({
        "Time Multipler": templateEvent["sessions"][0]["timeMultiplier"],
        "Hour of Day": templateEvent["sessions"][0]["hourOfDay"]
    })
    with open(accServerPathCfg + 'event.json', 'w') as outfile:
        json.dump(templateEvent, outfile)
        outfile.close()
    return eventInfo

def makeNewRace(carsData, raceNumber) : 
    """ Create random entrylist + random track and cars """
    with open(dataPath + 'defaultEntryList.json') as json_file:
        tempEntry = json.load(json_file)
        entryList = []
        # Iterate over all the items in dictionary and filter items which has even keys
        for user in tempEntry:
            if user['available']:
                entryList.append(user)

        json_file.close()
    # Get admin id
    with open(dataPath + 'championnshipConfiguration.json') as json_file:
        championnshipData = json.load(json_file)
        json_file.close()
    adminId = championnshipData['serverAdmin']
    # choose car class
    carList = []
    for car in carsData :
        if carsData[car]["available"]:
            carList.append(car)
    carClass = random.choice(carList)
    carClass = carsData[carClass]["class"]
    carClassList = dict(filter(lambda elem: elem[1]["class"] == carClass and elem[1]["available"],carsData.items()))
    #First race
    if raceNumber == 1:
        random.shuffle(entryList)
    #next race
    else :
        with open(dataPath + 'result.json') as json_file:
            resultData = json.load(json_file)
            json_file.close()
        currentNbDriver = len(resultData['championnshipStanding'])
        j = 1
        for driverData in entryList:
            driver_position = next((index for (index, d) in enumerate(resultData['championnshipStanding']) if d["playerId"] == 'S' + driverData['Steam id ']), -1) 
            if driver_position == -1 :
                driverData['position'] = currentNbDriver + j 
                j+= 1
            else :
                driverData['position'] = currentNbDriver - driver_position 
                driverData['ballast'] = int(resultData['championnshipStanding'][driver_position]['point'])
        entryList = sorted(entryList, key=lambda k: k['position']) 

    finalEntryList = {
        "entries" : [],
        "forceEntryList": 1
    }
    finalUserInfo = []
    startingPlace = 1
    for userData in entryList :
        userCar = random.choice(list(carClassList.keys()))
        userData['restrictor'] = 0
        if "ballast" not in userData:
            userData['ballast'] = 0
        elif userData['ballast'] > ballastInGameLimit :
            userData['restrictor'] = int((userData['ballast'] - ballastInGameLimit) / 3)
            if userData['restrictor'] > 20 :
                userData['restrictor'] = 20
            userData['ballast'] = ballastInGameLimit
        userEntry = {
            "drivers" : [{
                "firstName": userData["First name"],
                "lastName": userData["Surname"],
                "playerID": "S" + userData["Steam id "],
            }],
            "forcedCarModel": int(userCar),
            "overrideDriverInfo": 1,
            "ballastKg" : userData['ballast'],
            "restrictor" : userData['restrictor'],
            "defaultGridPosition": startingPlace
        }
        userInfo = {
            "firstName": userData["First name"],
            "lastName": userData["Surname"],
            "starting_place": startingPlace,
            "car" : carClassList[userCar]["model"],
            "ballast" : userData['ballast'],
            "restrictor" : userData['restrictor'],
            "playerID": userData["Steam id "]
        }
        # I put myself as admin
        if userData["Steam id "] == adminId :
            userEntry["isServerAdmin"] = 1
        finalEntryList["entries"].append(userEntry)
        finalUserInfo.append(userInfo)
        startingPlace += 1
        # if len(carClassList) > 1:
        #     carClassList.pop(userCar)

    with open(accServerPathCfg + 'entrylist.json', 'w') as outfile:
        json.dump(finalEntryList, outfile)
        outfile.close()
    return finalUserInfo

def nextRound(isFirstRound = False, isNewDraw=False):
    print("nextRound")
    carsData, trackData, weatherData = init()
    roundNumber = 1 if isFirstRound else 2
    info =  "A new Championnship has begun !" if isFirstRound else  "A new round has begun !"
    #Be sure to have the right json
    if isFirstRound : 
        olderResult = {}
        olderResult["championnshipStanding"] = olderResult["raceResult"] = olderResult["trackList"] = []
        with open(dataPath + 'result.json', 'w') as outfile:
            json.dump(olderResult, outfile)
            outfile.close()
    usersInfo = makeNewRace(carsData, roundNumber)
    eventConfig = makeEventConfig(trackData, weatherData)
    nextRoundInfo = {
        "eventInfo": eventConfig,
        "usersInfo": usersInfo,
        "foundNewResults" : info
    }
        # Save next round config
    with open(savesPath + 'nextRound.json', 'w') as outfile:
        json.dump(nextRoundInfo, outfile)
        outfile.close()
    if isNewDraw:
        Info.server_side_event(nextRoundInfo, 'newDraw') 
    return nextRoundInfo

def checkResult():
    #Check the server status
    serverStatus = False
    if "accServer.exe" in (p.name() for p in psutil.process_iter()) : 
        serverStatus = True
    #Check new race file in the server folder
    onlyfiles = [f for f in listdir(accServerPathResult) if isfile(join(accServerPathResult, f))]
    raceFile = ""
    for fileName in onlyfiles:
        splitList = fileName.split("_")
        if splitList[2] == "R.json":
            raceFile = fileName
    with open(dataPath + 'result.json') as json_file:
        olderResult = json.load(json_file)
        json_file.close()
    #if a result file is found
    if len(raceFile) > 0 :
        with open(accServerPathResult + raceFile, 'r', encoding="utf-16-le") as json_file: #accServerPathResult + raceFile
            correctFile = json_file.read()
            resultFile = json.loads(correctFile)
            json_file.close()

        with open(dataPath + 'championnshipConfiguration.json') as json_file:
            championnshipData = json.load(json_file)
            json_file.close()
        with open(savesPath + 'nextRound.json') as json_file:
            entryRaceData = json.load(json_file)
            json_file.close()

        raceNumber = len(olderResult['raceResult']) + 1 
        currentResult = []
        driverStandings = {}
        entryTrack = entryRaceData['eventInfo']['track']
        pos = 1
        index = 0    
        #List driver and pos before current race
        for driver in olderResult['championnshipStanding']:
            driverId = driver["playerId"]
            driverStandings[driverId] = index
            index += 1

        for driverResult in resultFile["sessionResult"]["leaderBoardLines"]:
            #Set race point
            if pos <= len(championnshipData["pointConfiguration"]):
                racePoint = championnshipData["pointConfiguration"][pos - 1]
            else :
                racePoint = 0
            #race result
            driverResult["currentDriver"]["position"] = pos
            driverResult["currentDriver"]["point"] = racePoint
            #Search his car and starting pos
            entryDriver = next(item for item in entryRaceData['usersInfo'] if 'S' + item["playerID"] == driverResult["currentDriver"]["playerId"])
            driverResult["currentDriver"]["carName"] = entryDriver['car']
            driverResult["currentDriver"]["starting_place"] = entryDriver['starting_place']
            currentResult.append(driverResult["currentDriver"])
            #championnship Standing
            driverId = driverResult["currentDriver"]["playerId"]
            if driverId in driverStandings:
                olderResult['championnshipStanding'][driverStandings[driverId]]['point'] += racePoint
            else :
                driverResult["currentDriver"]["point"] = racePoint
                olderResult['championnshipStanding'].append(driverResult["currentDriver"])
            pos +=1
        olderResult["raceResult"].append({
            raceNumber : currentResult
        })
        olderResult["trackList"].append(entryTrack)

        #Sort standings
        olderResult['championnshipStanding'] = sorted(olderResult['championnshipStanding'], key=lambda k: k['point'], reverse=True) 
        with open(dataPath + 'result.json', 'w') as outfile:
            json.dump(olderResult, outfile)
            outfile.close()
        #Cut and paste race result file in saves folder
        os.renames(accServerPathResult + raceFile, savesPath + raceFile)
        #Prepare next race
        nextRoundInfo = nextRound()
        raceNumber = str(raceNumber + 1)
        response = {
            "standings" : olderResult,
            "nextRoundInfo" : nextRoundInfo,
            "foundNewResults" : "New results has been found. Race " + raceNumber + " informations are available",
            "serverStatus" : serverStatus
            }
        Info.server_side_event(response, 'dataUpdate') 
        return response
    elif isfile(savesPath + 'nextRound.json'):
        with open(savesPath + 'nextRound.json') as json_file:
            nextRoundInfo = json.load(json_file)
            json_file.close()
        if olderResult['championnshipStanding'] == []:
            olderResult = None
        return {
            "standings" : olderResult,
            "nextRoundInfo" : nextRoundInfo,
            "foundNewResults" : False,
            "serverStatus" : serverStatus
        }
    #No current championnship
    else :
        return {
            "standings" : None,
            "nextRoundInfo" : None,
            "foundNewResults" : False,
            "serverStatus" : serverStatus
        }
def resetChampionnship():
    with open(dataPath + 'result.json') as json_file:
        olderResult = json.load(json_file)
        json_file.close()
    #remove saves file
    onlyfiles = [f for f in listdir(savesPath) if isfile(join(savesPath, f))]
    for fileName in onlyfiles:
        splitList = fileName.split("_")
        if len(splitList) >= 3 and splitList[2] == "R.json":
            os.remove(savesPath + fileName)
    os.remove(savesPath + "nextRound.json")
    #save final result
    saveName = 'finalSave_' + today.strftime("%d_%m_%Y") + '.json'
    with open(savesPath + saveName, 'w') as outfile:
        json.dump(olderResult, outfile)
        outfile.close()
    olderResult["championnshipStanding"] = olderResult["raceResult"] = olderResult["trackList"] = []
    with open(dataPath + 'result.json', 'w') as outfile:
        json.dump(olderResult, outfile)
        outfile.close()
    return True

def getParams():
    paramList = {}
    with open(dataPath + 'availableParameters.json') as json_file:
        paramList['paramList'] = json.load(json_file)
        json_file.close()
    for fileName in paramList['paramList']:
        with open(fileName) as json_file:
            currentValues = json.load(json_file)
            json_file.close()
        for param in paramList['paramList'][fileName]: 
            if param['name'] == 'practiceDuration' : 
                param['currentValue'] = currentValues['sessions'][0]['sessionDurationMinutes']
            elif param['name'] == 'raceDuration' : 
                param['currentValue'] = currentValues['sessions'][1]['sessionDurationMinutes']
            else :
                param['currentValue'] = currentValues[param['name']]
    with open(dataPath + 'cars.json') as json_file:
        paramList['cars'] = json.load(json_file)
        json_file.close()
    with open(dataPath + 'tracks.json') as json_file:
        paramList['tracks'] = json.load(json_file)
        json_file.close()
    with open(dataPath + 'defaultEntryList.json') as json_file:
        paramList['entry'] = json.load(json_file)
        json_file.close()
    return paramList


def updateParameters(newParameters):
    #update and write new parameter
    for param in newParameters:
        with open(param['file'], 'r') as json_file:
            olderValue = json.load(json_file)
            if param['name'] == 'pointConfiguration' and type(param['value']) is str: 
                param['value'] = param['value'].split(',')
                param['value'] = [int(i) for i in param['value']]
            #update the good field
            if param['name'] == 'practiceDuration': 
                olderValue['sessions'][0]['sessionDurationMinutes'] = param['value']
            elif param['name'] == 'raceDuration' :
                olderValue['sessions'][1]['sessionDurationMinutes'] = param['value']
            else :
                olderValue.update({param['name'] : param['value']})
            json_file.close()
        with open(param['file'], 'w') as json_file:
            json.dump(olderValue, json_file)
            json_file.close()
def updateTrackParameters(newParameters):
    #update and write new parameter
    with open(dataPath + "tracks.json", 'r') as json_file:
        trackList = json.load(json_file)
        json_file.close()
    
    for param in newParameters:
        trackList[param["index"]]["available"] = param["available"]

    with open(dataPath + "tracks.json", 'w') as json_file:
        json.dump(trackList, json_file)
        json_file.close()
def updateCarParameters(newParameters):
    #update and write new parameter
    with open(dataPath + "cars.json", 'r') as json_file:
        carList = json.load(json_file)
        json_file.close()
    
    for param in newParameters:
        carList[param["index"]]["available"] = param["available"]

    with open(dataPath + "cars.json", 'w') as json_file:
        json.dump(carList, json_file)
        json_file.close()
def updateEntryParameters(newParameters):
    #update and write new parameter
    with open(dataPath + "defaultEntryList.json", 'r') as json_file:
        entryList = json.load(json_file)
        json_file.close()
    i = 0
    for param in newParameters:
        entryList[i]["available"] = param["available"]
        i += 1

    with open(dataPath + "defaultEntryList.json", 'w') as json_file:
        json.dump(entryList, json_file)
        json_file.close()
def getOlderResult():
    onlyfiles = [f for f in listdir(savesPath) if isfile(join(savesPath, f))]
    allResults = []
    raceFile = []
    #retrieve all finalSave file
    for fileName in onlyfiles:
        splitList = fileName.split("_")
        if splitList[0] == "finalSave":
            with open(savesPath + fileName, 'r') as json_file:
                olderResult = json.load(json_file)
                json_file.close() 
            olderResult['date'] = splitList[1] + '/' + splitList[2] + '/' + splitList[3].replace('.json', '')
            
            allResults.append(olderResult)
            # raceFile.append(fileName)
    #Sorte result by datetime
    allResults = sorted(allResults, key=lambda k:  datetime.strptime(k['date'], "%d/%m/%Y"))
    return allResults


def launchServer():
    """ Call a powershell script to launch the server """
        #Save every config files in the server folder
    for fileName in configFiles:
        os.remove(accServerPathCfg + fileName)
        copyfile(templatePath + fileName, accServerPathCfg + fileName)
    subprocess.call('start "" "D:\Steam\steamapps\common\Assetto Corsa Competizione Dedicated Server\server/launch_server.sh"', shell=True)

    Info.server_side_event({
        "serverStatus": True
    }, 'updateServerStatus') 
    return {"serverStatus" : True}

def shutDownServer():
    """ shut Down the server """
        #Save every config files in the server folder
    if "accServer.exe" in (p.name() for p in psutil.process_iter()) : 
        os.system("TASKKILL /F /IM accServer.exe")
    Info.server_side_event({
        "serverStatus": False
    }, "updateServerStatus") 
    return {"serverStatus" : False}