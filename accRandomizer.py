import json
import random
from os import listdir
from os.path import isfile, join
import subprocess
import os
from shutil import copyfile
from datetime import date
import psutil

import infoApi as Info
from datetime import datetime
from numpy.random import choice
from math import *
import time
from dotenv import dotenv_values

config = dotenv_values(".env")
today = date.today()
try:
    accServerPath = config['ACC_SERVER_PATH']
except:
    raise ValueError("You must enter your acc server path in the .env file")

accServerPathCfg = accServerPath + "cfg/"
accServerPathResult = accServerPath + "results/"
dataPath = "Data/"
templatePath = "Template/"
savesPath = "saves/"
# Static cfg files, just need to put in the server folder
configFiles = ["assistRules.json", "configuration.json", "settings.json"]  #
ballastInGameLimit = 40
ballastMinValue = -40
server = None
ballastList = [40, 35, 30, 25, 20, 15, 10, 5, 0, -5, -10, -15, -20, -25, -30, -35, -40]

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


def makeEventConfig(trackData, weatherData, championnshipConfiguration, customEvent):
    """ Create event and assist file from template"""
    weatherWeightConfig = championnshipConfiguration['weatherWeightConfiguration']
    weatherName = championnshipConfiguration['weatherPresetName']
    with open(templatePath + 'event.json') as json_file1:
        templateEvent = json.load(json_file1)
        json_file1.close()
    eventInfo = {}
    # Choose track
    if customEvent == {}:
        trackList = []
        for track in trackData:
            if trackData[track]["available"]:
                trackList.append(track)
        listTrack = random.choice(trackList)
        finalTrack = random.choice(trackData[listTrack]["tracks"])
    else:
        finalTrack = trackData
    templateEvent["track"] = finalTrack
    eventInfo["track"] = finalTrack

    draw = [len(weatherWeightConfig) - 1]
    # Choose pre-configuration
    if customEvent == {}:
        if len(weatherWeightConfig) == len(weatherData):
            weatherWeightPct = []
            total = sum(weatherWeightConfig)
            if total != 0:
                for weight in weatherWeightConfig:
                    weatherWeightPct.append(round(weight / total, 3))
                totalWeightMissing = round(1 - sum(weatherWeightPct), 3)
                weatherWeightPct[len(weatherWeightConfig) -
                                 1] += totalWeightMissing
                draw = choice(len(weatherWeightConfig), 1, p=weatherWeightPct)

        weatherWeightConfig[draw[0]] -= 1
        championnshipConfiguration['weatherWeightConfiguration'] = weatherWeightConfig
        weatherData = weatherData[weatherName[draw[0]]]
    # else weatherData is already matching custom event

    # Choose weather
    templateEvent["ambientTemp"] = random.randint(
        weatherData['ambientTemp']["min"], weatherData['ambientTemp']["max"])
    templateEvent["cloudLevel"] = round(
        random.uniform(weatherData['cloudLevel']["min"], weatherData['cloudLevel']["max"]), 1)
    # Choose rain level
    rain = round(random.uniform(
        weatherData['rain']["min"], weatherData['rain']["max"]), 1)
    templateEvent["rain"] = rain
    templateEvent["weatherRandomness"] = random.randint(weatherData['weatherRandomness']["min"],
                                                        weatherData['weatherRandomness']["max"])
    eventInfo.update({
        "Ambient temperature": templateEvent["ambientTemp"],
        "Cloud level": templateEvent["cloudLevel"],
        "Rain": templateEvent["rain"],
        "Weather randomness": templateEvent["weatherRandomness"]
    })

    # Choose daytime
    if customEvent == {}:
        timeBegin = 10
        timeEnd = 23
    else:
        # INVERTED MAYBE NEED FIX
        if not customEvent['dayTime']:
            timeBegin = 9
            timeEnd = 16
        else:
            timeBegin = 0
            timeEnd = 3

    daytime = random.randint(timeBegin, timeEnd)
    timeMultipler = random.randint(3, 15)
    templateEvent["sessions"][0]["hourOfDay"] = templateEvent["sessions"][1]["hourOfDay"] = daytime
    templateEvent["sessions"][0]["timeMultiplier"] = templateEvent["sessions"][1]["timeMultiplier"] = timeMultipler
    eventInfo.update({
        "Time Multipler": templateEvent["sessions"][0]["timeMultiplier"],
        "Hour of Day": templateEvent["sessions"][0]["hourOfDay"]
    })

    # update probability
    with open(dataPath + 'championnshipConfiguration.json', 'w') as outfile:
        json.dump(championnshipConfiguration, outfile)
        outfile.close()

    with open(accServerPathCfg + 'event.json', 'w') as outfile:
        json.dump(templateEvent, outfile)
        outfile.close()
    return eventInfo


def makeNewRace(carsData, raceNumber):
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
    # check if custom event and car list is list
    if isinstance(carsData, list):
        tempCarData = {}
        for car in carsData:
            tempCarData.update({car['index']: car})
        carsData = tempCarData

    for car in carsData:
        if carsData[car]["available"]:
            carList.append(car)

    carClass = random.choice(carList)
    carClass = carsData[carClass]["class"]
    carClassList = dict(filter(
        lambda elem: elem[1]["class"] == carClass and elem[1]["available"], carsData.items()))
    # First race
    if raceNumber == 1:
        random.shuffle(entryList)
    # next race ==> Sort entry list in reverse championnship grid
    else:
        with open(dataPath + 'result.json') as json_file:
            resultData = json.load(json_file)
            json_file.close()
        currentNbDriver = len(resultData['championnshipStanding'])
        j = 1
        for driverData in entryList:
            driver_position = next((index for (index, d) in enumerate(resultData['championnshipStanding']) if
                                    d["playerId"] == 'S' + driverData['Steam id ']), -1)
            if driver_position == -1:
                driverData['position'] = currentNbDriver + j
                j += 1
            else:
                driverData['position'] = currentNbDriver - driver_position
                if driver_position >= len(ballastList):
                    ballast = ballastMinValue
                else:
                    ballast = ballastList[driver_position]
                # ballast = int(round(int(resultData['championnshipStanding'][driver_position]['point'] / 2) + (
                #             10 - driver_position * 1.5), 0))

                driverData['ballast'] = ballast if ballast > ballastMinValue else ballastMinValue
        entryList = sorted(entryList, key=lambda k: k['position'])

    finalEntryList = {
        "entries": [],
        "forceEntryList": 1
    }
    finalUserInfo = []
    startingPlace = 1
    nbDriver = len(entryList)
    for userData in entryList:
        userCar = random.choice(list(carClassList.keys()))

        userData['restrictor'] = 0
        if "ballast" not in userData:
            # If the user is not in the champ
            userData['ballast'] = 0
        elif userData['ballast'] > ballastInGameLimit:
            userData['restrictor'] = int(
                (userData['ballast'] - ballastInGameLimit) / 3)
            if userData['restrictor'] > 20:
                userData['restrictor'] = 20
            userData['ballast'] = ballastInGameLimit
        # Determine driver class : First tier = Amateur, Second Tier = Silver, Final = Pro
        if startingPlace < nbDriver / 3:
            driverCategorie = 0
        elif startingPlace < (nbDriver / 3 * 2):
            driverCategorie = 1
        else:
            driverCategorie = 2
        userEntry = {
            "drivers": [{
                "firstName": userData["First name"],
                "lastName": userData["Surname"],
                "playerID": "S" + userData["Steam id "],
                "driverCategory": driverCategorie
            }],
            "forcedCarModel": int(userCar),
            "overrideDriverInfo": 1,
            "ballastKg": userData['ballast'],
            "restrictor": userData['restrictor'],
            "defaultGridPosition": startingPlace
        }
        userInfo = {
            "firstName": userData["First name"],
            "lastName": userData["Surname"],
            "starting_place": startingPlace,
            "car": carClassList[userCar]["model"],
            "ballast": userData['ballast'],
            "restrictor": userData['restrictor'],
            "playerID": userData["Steam id "],
            "nationality": userData["Nationality"] if "Nationality" in userData else "Unknown"
        }
        # I put myself as admin
        if userData["Steam id "] == adminId:
            userEntry["isServerAdmin"] = 1
        # Forced race number
        if "Race number" in userData:
            userEntry["raceNumber"] = int(userData['Race number'])
        finalEntryList["entries"].append(userEntry)
        finalUserInfo.append(userInfo)
        startingPlace += 1
        # if len(carClassList) > 1:
        #     carClassList.pop(userCar)

    return {
        'usersInfo': finalUserInfo,
        'finalEntryList': finalEntryList
    }


def nextRound(isFirstRound=False, isNewDraw=False, customEvent={}, keepTeamWith = False):
    carsData, trackData, weatherData = init()
    roundNumber = 1 if isFirstRound else 2
    info = "A new Championnship has begun !" if isFirstRound else "A new round has begun !"
    if customEvent != {}:
        carsData = customEvent['cars']
        trackData = customEvent['track']
        weatherData = weatherData[customEvent['weather']]
        info = "Welcome to " + customEvent['userName'] + " event !"

    # Be sure to have the right json
    with open(dataPath + 'championnshipConfiguration.json') as json_file:
        championnshipConfiguration = json.load(json_file)
        json_file.close()
    if isFirstRound:
        #Reset team with
        # reset joker number
        with open(dataPath + 'defaultEntryList.json') as json_file:
            entrylist = json.load(json_file)
            json_file.close()

        for i, driver in enumerate(entrylist):
            entrylist[i]['swapCar'] = championnshipConfiguration['swapCar']
            entrylist[i]['teamWith'] = championnshipConfiguration['teamWith']
            entrylist[i]['teamWithVictim'] = 0

        with open(dataPath + 'defaultEntryList.json', 'w') as outfile:
            json.dump(entrylist, outfile)
            outfile.close()

        olderResult = {}
        olderResult["championnshipStanding"] = olderResult["raceResult"] = olderResult["trackList"] = []
        with open(dataPath + 'result.json', 'w') as outfile:
            json.dump(olderResult, outfile)
            outfile.close()
    usersInfo = makeNewRace(carsData, roundNumber)
    eventConfig = makeEventConfig(
        trackData, weatherData, championnshipConfiguration, customEvent)
    teamWithArray = []
    if keepTeamWith:
        with open(savesPath + 'nextround.json') as json_file:
            nextroundInfo = json.load(json_file)
            json_file.close()
        teamWithArray = nextroundInfo["teamWith"]

    nextRoundInfo = {
        "eventInfo": eventConfig,
        "usersInfo": usersInfo,
        "foundNewResults": info,
        "teamWith": teamWithArray,
        "gridStatus" : "READY"
    }
    # Save next round config
    with open(accServerPathCfg + 'entrylist.json', 'w') as outfile:
        json.dump(usersInfo['finalEntryList'], outfile)
        outfile.close()
    with open(savesPath + 'nextRound.json', 'w') as outfile:
        json.dump(nextRoundInfo, outfile)
        outfile.close()
    if isNewDraw:
        Info.server_side_event(nextRoundInfo, 'newDraw')
    return nextRoundInfo


def checkResult():
    serverStatus = getServerStatus()
    # Check new race file in the server folder
    onlyfiles = [f for f in listdir(accServerPathResult) if isfile(
        join(accServerPathResult, f))]
    raceFile = ""
    for fileName in onlyfiles:
        splitList = fileName.split("_")
        if splitList[2] == "R.json":
            raceFile = fileName
    with open(dataPath + 'result.json') as json_file:
        olderResult = json.load(json_file)
        json_file.close()
    # if a result file is found
    if len(raceFile) > 0:
        with open(accServerPathResult + raceFile, 'r',
                  encoding="utf-16-le") as json_file:  # accServerPathResult + raceFile
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
        globalPos = 1
        index = 0
        listTeamWith = entryRaceData['teamWith']
        # List driver and pos before current race
        for driver in olderResult['championnshipStanding']:
            driverId = driver["playerId"]
            driverStandings[driverId] = index
            index += 1
        #List all drivers registered for previous race
        driverRegistered = entryRaceData['usersInfo']['usersInfo']
        for driverResult in resultFile["sessionResult"]["leaderBoardLines"]:

            # Search his car and starting pos
            entryDriver = next(item for item in entryRaceData['usersInfo']['usersInfo'] if
                               'S' + item["playerID"] == driverResult["currentDriver"]["playerId"])
            #Delet driver from registered list
            driverRegistered = [i for i in driverRegistered if not (i["playerID"] == entryDriver["playerID"])]
            driverId = entryDriver['playerID']
            pos = globalPos
            #Compute team with
            teamWithTupleInfo = None
            for tupleTeamWith in listTeamWith:
                if driverId in tupleTeamWith:
                    teamWithTupleInfo = tupleTeamWith
            #Check if in team with
            if teamWithTupleInfo is not None:
                teammateId = teamWithTupleInfo[1] if driverId == teamWithTupleInfo[0] else teamWithTupleInfo[0]
                teammateInfo = next((item for item in resultFile["sessionResult"]["leaderBoardLines"] if
                               item["currentDriver"]["playerId"] == "S" + teammateId), None)
                if teammateInfo is not None:
                    teammatePos = next((index for (index, d) in enumerate(resultFile["sessionResult"]["leaderBoardLines"]) if d == teammateInfo), None)
                    #Index to real pos
                    teammatePos += 1
                    leaderPoint = championnshipData["pointConfiguration"][pos - 1] if pos <= len(championnshipData["pointConfiguration"]) else 0
                    teammatePoint = championnshipData["pointConfiguration"][teammatePos - 1] if teammatePos <= len(championnshipData["pointConfiguration"]) else 0
                    racePoint = round((teammatePoint + leaderPoint)/2, 0)
                else:
                    # Set race point casually because teammate wasn't in the race
                    if pos <= len(championnshipData["pointConfiguration"]):
                        racePoint = championnshipData["pointConfiguration"][pos - 1]
                    else:
                        racePoint = 0
            else:
                # Set race point
                if pos <= len(championnshipData["pointConfiguration"]):
                    racePoint = championnshipData["pointConfiguration"][pos - 1]
                else:
                    racePoint = 0
            globalPos += 1
            # race result
            driverResult["currentDriver"]["position"] = pos
            driverResult["currentDriver"]["point"] = racePoint

            driverResult["currentDriver"]["carName"] = entryDriver['car']
            driverResult["currentDriver"]["starting_place"] = entryDriver['starting_place']

            currentResult.append(driverResult["currentDriver"])
            # championnship Standing
            driverId = driverResult["currentDriver"]["playerId"]
            if driverId in driverStandings:
                olderResult['championnshipStanding'][driverStandings[driverId]
                ]['point'] += racePoint
            else:
                driverResult["currentDriver"]["point"] = racePoint
                olderResult['championnshipStanding'].append(
                    driverResult["currentDriver"])

        with open(dataPath + 'defaultEntryList.json') as json_file:
            defaultEntry = json.load(json_file)
            json_file.close()
        # Driver who not participated
        for driverInfo in driverRegistered:
            driverToUpdateIndex = next((i for i, item in enumerate(
                defaultEntry) if item['Steam id '] == driverInfo["playerID"]), None)
            if driverToUpdateIndex is not None:
                defaultEntry[driverToUpdateIndex]["available"] = False
        with open(dataPath + "defaultEntryList.json", 'w') as json_file:
            json.dump(defaultEntry, json_file)
            json_file.close()
        olderResult["raceResult"].append({
            raceNumber: currentResult
        })
        olderResult["trackList"].append(entryTrack)

        # Sort standings
        olderResult['championnshipStanding'] = sorted(olderResult['championnshipStanding'], key=lambda k: k['point'],
                                                      reverse=True)
        entryRaceData["gridStatus"] = "WAITING_NEW_DRAW"
        # removed teammate jokers list
        entryRaceData["teamWith"] = []
        #Store status in the nextRound.json
        with open(savesPath + 'nextRound.json', 'w') as outfile:
            json.dump(entryRaceData, outfile)
            json_file.close()

        with open(dataPath + 'result.json', 'w') as outfile:
            json.dump(olderResult, outfile)
            outfile.close()
        # Cut and paste race result file in saves folder
        os.renames(accServerPathResult + raceFile, savesPath + raceFile)

        # Prepare next race<
        # nextRoundInfo = nextRound()
        nextRoundInfo = {}
        raceNumber = str(raceNumber + 1)


        response = {
            "standings": olderResult,
            "nextRoundInfo": nextRoundInfo,
            "foundNewResults": "New results has been found.",
            "serverStatus": serverStatus,
            "gridStatus" : "WAITING_NEW_DRAW"
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
            "standings": olderResult,
            "nextRoundInfo": nextRoundInfo,
            "foundNewResults": False,
            "serverStatus": serverStatus,
            "gridStatus" : nextRoundInfo["gridStatus"]
        }
    # No current championnship
    else:
        return {
            "standings": None,
            "nextRoundInfo": None,
            "foundNewResults": False,
            "serverStatus": serverStatus,
            "gridStatus": "WAITING_NEW_DRAW"
        }


def resetChampionnship():
    with open(dataPath + 'result.json') as json_file:
        olderResult = json.load(json_file)
        json_file.close()
    # remove saves file
    onlyfiles = [f for f in listdir(savesPath) if isfile(join(savesPath, f))]
    for fileName in onlyfiles:
        splitList = fileName.split("_")
        if len(splitList) >= 3 and splitList[2] == "R.json":
            os.remove(savesPath + fileName)
    os.remove(savesPath + "nextRound.json")
    # save final result
    saveName = 'finalSave_' + today.strftime("%d_%m_%Y") + '.json'
    with open(savesPath + saveName, 'w') as outfile:
        json.dump(olderResult, outfile)
        outfile.close()
    olderResult["championnshipStanding"] = olderResult["raceResult"] = olderResult["trackList"] = []
    with open(dataPath + 'result.json', 'w') as outfile:
        json.dump(olderResult, outfile)
        outfile.close()
    return True


def getCountdown():
    with open(dataPath + 'championnshipConfiguration.json') as json_file:
        config = json.load(json_file)
        json_file.close()
    return config['swapCountDown']


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
            if param['name'] == 'practiceDuration':
                param['currentValue'] = currentValues['sessions'][0]['sessionDurationMinutes']
            elif param['name'] == 'raceDuration':
                param['currentValue'] = currentValues['sessions'][1]['sessionDurationMinutes']
            else:
                param['currentValue'] = currentValues[param['name']]
    with open(dataPath + 'cars.json') as json_file:
        paramList['cars'] = json.load(json_file)
        json_file.close()
    with open(dataPath + 'tracks.json') as json_file:
        paramList['tracks'] = json.load(json_file)
        json_file.close()
    with open(dataPath + 'weatherConfiguration.json') as json_file:
        paramList['weather'] = json.load(json_file)
        json_file.close()
    with open(dataPath + 'defaultEntryList.json') as json_file:
        paramList['entry'] = json.load(json_file)
        json_file.close()
    return paramList


def updateParameters(newParameters):
    # update and write new parameter
    for param in newParameters:
        with open(param['file'], 'r') as json_file:
            olderValue = json.load(json_file)
            if param['name'] in ['pointConfiguration', 'weatherWeightConfiguration'] and type(param['value']) is str:
                param['value'] = param['value'].split(',')
                param['value'] = [int(i) for i in param['value']]
            # update the good field
            if param['name'] == 'practiceDuration':
                olderValue['sessions'][0]['sessionDurationMinutes'] = param['value']
            elif param['name'] == 'raceDuration':
                olderValue['sessions'][1]['sessionDurationMinutes'] = param['value']
            else:
                olderValue.update({param['name']: param['value']})
            json_file.close()
        with open(param['file'], 'w') as json_file:
            json.dump(olderValue, json_file)
            json_file.close()


def updateTrackParameters(newParameters):
    # update and write new parameter
    with open(dataPath + "tracks.json", 'r') as json_file:
        trackList = json.load(json_file)
        json_file.close()

    for param in newParameters:
        trackList[param["index"]]["available"] = param["available"]

    with open(dataPath + "tracks.json", 'w') as json_file:
        json.dump(trackList, json_file)
        json_file.close()


def updateCarParameters(newParameters):
    # update and write new parameter
    with open(dataPath + "cars.json", 'r') as json_file:
        carList = json.load(json_file)
        json_file.close()

    for param in newParameters:
        carList[param["index"]]["available"] = param["available"]

    with open(dataPath + "cars.json", 'w') as json_file:
        json.dump(carList, json_file)
        json_file.close()


def updateEntryParameters(newParameters, singleUpdate=False):
    # update and write new parameter
    with open(dataPath + "defaultEntryList.json", 'r') as json_file:
        entryList = json.load(json_file)
        json_file.close()
    i = 0
    # Find and update availability of someone after hitting the button "not in grid"
    if singleUpdate:
        driverToUpdateIndex = next((i for i, item in enumerate(
            entryList) if item['Steam id '] == newParameters), None)
        if driverToUpdateIndex is not None:
            entryList[driverToUpdateIndex]["available"] = True
    else:
        for param in newParameters:
            entryList[i]["available"] = param["available"]
            i += 1

    with open(dataPath + "defaultEntryList.json", 'w') as json_file:
        json.dump(entryList, json_file)
        json_file.close()
    return entryList


def swapCar(parameters):
    #If the server is up, no swap available
    if not getServerStatus():
        with open(dataPath + "defaultEntryList.json", 'r') as json_file:
            userList = json.load(json_file)
            json_file.close()
        with open(savesPath + "nextRound.json", 'r') as json_file:
            roundInfo = json.load(json_file)
            json_file.close()
        # MAKE A NEW ENTRYLIST
        entryList = roundInfo['usersInfo']['finalEntryList']['entries']
        driverOne = next((i for i, item in enumerate(entryList) if item['drivers'][0]['playerID'] == "S" + parameters[0]),
                         None)
        carOne = entryList[driverOne]['forcedCarModel']
        driverTwo = next((i for i, item in enumerate(entryList) if item['drivers'][0]['playerID'] == "S" + parameters[1]),
                         None)
        carTwo = entryList[driverTwo]['forcedCarModel']
        entryList[driverOne]['forcedCarModel'] = carTwo
        entryList[driverTwo]['forcedCarModel'] = carOne
        roundInfo['usersInfo']['finalEntryList']['entries'] = entryList

        # MAKE A NEW USERINFO
        userInfo = roundInfo['usersInfo']['usersInfo']
        driverOne = next((i for i, item in enumerate(userInfo)
                          if item['playerID'] == parameters[0]), None)
        carOne = userInfo[driverOne]['car']
        driverTwo = next((i for i, item in enumerate(userInfo)
                          if item['playerID'] == parameters[1]), None)
        carTwo = userInfo[driverTwo]['car']
        userInfo[driverOne]['car'] = carTwo
        userInfo[driverTwo]['car'] = carOne
        roundInfo['usersInfo']['usersInfo'] = userInfo

        # Decrease joker counter
        driverOne = next((i for i, item in enumerate(userList)
                          if item['Steam id '] == parameters[0]), None)
        userList[driverOne]['swapCar'] -= 1

        with open(savesPath + "nextRound.json", 'w') as json_file:
            json.dump(roundInfo, json_file)
            json_file.close()

        with open(accServerPathCfg + 'entrylist.json', 'w') as outfile:
            json.dump(roundInfo['usersInfo']['finalEntryList'], outfile)
            outfile.close()

        with open(dataPath + "defaultEntryList.json", 'w') as outfile:
            json.dump(userList, outfile)
            outfile.close()

        # Update everyone screen
        nextRoundInfo = checkResult()
        infoJustSwapped = {
            "nri" : nextRoundInfo,
            "leader" : {
                "id" : parameters[0],
                "name" : str(userList[driverOne]["First name"] + " " + userList[driverOne]["Surname"])
            },
            "victim": {
                "id": parameters[1],
                "name": str(userInfo[driverTwo]["firstName"] + " " + userInfo[driverTwo]["lastName"])
            },
            "action" : "swapCar"
        }
        Info.server_side_event(infoJustSwapped, 'justSwapped')
    return True


def teamWith(parameters):
    if not getServerStatus():
        with open(dataPath + "defaultEntryList.json", 'r') as json_file:
            userList = json.load(json_file)
            json_file.close()

        with open(savesPath + "nextRound.json", 'r') as json_file:
            roundInfo = json.load(json_file)
            json_file.close()

        #Check if already in a team
        for tupleDrivers in roundInfo['teamWith']:
            if parameters[0] in tupleDrivers or parameters[1] in tupleDrivers:
                print(parameters + " ALREADY IN A TEAM")
                return False

        roundInfo['teamWith'].append(parameters)

        # Decrease joker counter
        driverOne = next((i for i, item in enumerate(userList)
                          if item['Steam id '] == parameters[0]), None)
        driverVictim = next((i for i, item in enumerate(
            userList) if item['Steam id '] == parameters[1]), None)
        userList[driverOne]['teamWith'] -= 1
        userList[driverVictim]['teamWithVictim'] += 1

        with open(savesPath + "nextRound.json", 'w') as json_file:
            json.dump(roundInfo, json_file)
            json_file.close()

        with open(dataPath + "defaultEntryList.json", 'w') as outfile:
            json.dump(userList, outfile)
            outfile.close()

        nextRoundInfo = checkResult()
        infoJustSwapped = {
            "nri" : nextRoundInfo,
            "leader" : {
                "id" : parameters[0],
                "name" : str(userList[driverOne]["First name"] + " " + userList[driverOne]["Surname"])
            },
            "victim": {
                "id": parameters[1],
                "name": str(userList[driverVictim]["First name"] + " " + userList[driverVictim]["Surname"])
            },
            "action" : "teamWith"
        }
        Info.server_side_event(infoJustSwapped, 'justSwapped')


def getTeamInfo():
    with open(savesPath + "nextRound.json", 'r') as json_file:
        roundInfo = json.load(json_file)
        json_file.close()
    # init variable to avoid error in case of not founding it
    teamInfos = []
    for item in roundInfo["teamWith"]:
        teamInfo = {
            "leader": item[0],
            "victim": item[1]
        }
        teamInfos.append(teamInfo)
    print("\n Team infos: " + str(teamInfos) + "\n")
    return teamInfos


def getOlderResult():
    onlyfiles = [f for f in listdir(savesPath) if isfile(join(savesPath, f))]
    allResults = []
    raceFile = []
    # retrieve all finalSave file
    for fileName in onlyfiles:
        splitList = fileName.split("_")
        if splitList[0] == "finalSave":
            with open(savesPath + fileName, 'r') as json_file:
                olderResult = json.load(json_file)
                json_file.close()
            olderResult['date'] = splitList[1] + '/' + \
                                  splitList[2] + '/' + splitList[3].replace('.json', '')
            allResults.append(olderResult)
            # raceFile.append(fileName)
    # Sorte result by datetime
    allResults = sorted(
        allResults, key=lambda k: datetime.strptime(k['date'], "%d/%m/%Y"))
    return allResults


def fetchDrivers():
    with open(dataPath + 'defaultEntryList.json') as json_file:
        entryList = json.load(json_file)
        json_file.close()
    return entryList


def fetchCustomEvent():
    with open(dataPath + 'defaultEntryList.json') as json_file:
        entryList = json.load(json_file)
    with open(dataPath + 'customEvent.json') as json_file:
        customEvent = json.load(json_file)
        customEventFinal = customEvent
        for custom in list(customEvent):
            driverInfo = next(
                item for item in entryList if item['Steam id '] == custom)
            if driverInfo['available'] == False:
                del customEvent[custom]
        json_file.close()
    return customEventFinal


def setNextRoundFromSpin(eventInfo):
    return nextRound(False, True, eventInfo, True)


def createCustomEvent(eventInfo):
    carsAvailable = []
    with open(dataPath + 'customEvent.json') as json_file:
        entryList = json.load(json_file)
        json_file.close()
    for cars in eventInfo['cars']:
        if cars['available']:
            carsAvailable.append(cars)

    eventInfo['cars'] = carsAvailable
    entryList[eventInfo['steam id ']] = eventInfo

    # entryList.update(eventInfo['steam id '])

    with open(dataPath + "customEvent.json", 'w') as json_file:
        json.dump(entryList, json_file)
        json_file.close()


def findSpotInGrid(userId):
    entryList = updateEntryParameters(userId, True)
    # get all car in the grid and choose one randomly
    userData = next(
        (item for item in entryList if item['Steam id '] == userId))
    with open(dataPath + 'cars.json') as json_file:
        carsData = json.load(json_file)
        json_file.close()
    with open(savesPath + 'nextRound.json') as json_file:
        nextRoundInfo = json.load(json_file)
        json_file.close()
    startingPlace = len(nextRoundInfo["usersInfo"]["usersInfo"]) + 1
    # gather all cars
    carList = []
    for userInfo in nextRoundInfo["usersInfo"]["finalEntryList"]["entries"]:
        carList.append(userInfo["forcedCarModel"])
    carList = list(dict.fromkeys(carList))
    carId = random.choice(carList)
    userInfo = {
        "firstName": userData["First name"],
        "lastName": userData["Surname"],
        "starting_place": startingPlace,
        "car": carsData[str(carId)]["model"],
        "ballast": ballastMinValue,
        "restrictor": 0,
        "playerID": userData["Steam id "],
        "nationality": userData["Nationality"] if "Nationality" in userData else "Unknown"
    }
    userEntry = {
        "drivers": [{
            "firstName": userData["First name"],
            "lastName": userData["Surname"],
            "playerID": "S" + userData["Steam id "],
            "driverCategory": 0
        }],
        "forcedCarModel": int(carId),
        "overrideDriverInfo": 1,
        "ballastKg": ballastMinValue,
        "restrictor": 0,
        "defaultGridPosition": startingPlace
    }
    # save in conf
    nextRoundInfo["usersInfo"]["usersInfo"].append(userInfo)
    nextRoundInfo["usersInfo"]["finalEntryList"]["entries"].append(userEntry)
    with open(accServerPathCfg + 'entrylist.json', 'w') as outfile:
        json.dump(nextRoundInfo["usersInfo"]["finalEntryList"], outfile)
        outfile.close()
    with open(savesPath + 'nextRound.json', 'w') as outfile:
        json.dump(nextRoundInfo, outfile)
        outfile.close()
    nextRoundInfo["foundNewResults"] = False
    Info.server_side_event(nextRoundInfo, 'newDraw')
    return nextRoundInfo


def log_subprocess_output(pipe):
    for line in iter(pipe.readline, b''):  # b'\n'-separated lines
        print('got line from subprocess: %r', line)


def launchServer():
    """ Call a powershell script to launch the server """
    # Wait one sec in case last second joker usage
    time.sleep(2)
    # Save every config files in the server folder
    for fileName in configFiles:
        os.remove(accServerPathCfg + fileName)
        copyfile(templatePath + fileName, accServerPathCfg + fileName)

    subprocess.Popen(
        'start "" "D:\Steam\steamapps\common\Assetto Corsa Competizione Dedicated Server\server/launch_server.sh"',
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    Info.server_side_event({
        "serverStatus": True
    }, 'updateServerStatus')
    return {"serverStatus": True}

def getServerStatus():
    # Check the server status
    serverStatus = False
    if "accServer.exe" in (p.name() for p in psutil.process_iter()):
        serverStatus = True
    return serverStatus
def shutDownServer():
    """ shut Down the server """
    # Save every config files in the server folder
    if getServerStatus():
        os.system("TASKKILL /F /IM accServer.exe")
    Info.server_side_event({
        "serverStatus": False
    }, "updateServerStatus")
    return {"serverStatus": False}

# checkResult()
# findSpotInGrid('76561197961422699')
# swapCar(['76561198445003541', '76561198278916703'])