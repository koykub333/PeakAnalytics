import requests
from datetime import datetime, timedelta

NHL_STATS_API_URL = "https://api-web.nhle.com"

def main():
    #processSeason(2023)
    processGame(2023020204)


#pullGameData does a get request on the NHL's
#   stats API and returns the data as a python
#   dictionary
# PARAMETERS:
#   -gameId: integer representation of the
#       desired game's ID number
# RETURNS:
#   -dictionary containing all of the game data
def pullGameData(gameId):
    response = requests.get(NHL_STATS_API_URL+"/v1/gamecenter/"+str(gameId)+"/play-by-play")
    return response.json()


#pullGameShifts does a get request on the NHL's
#   stats API and returns the shifts as a list
#   sorted by shift start time
# PARAMETERS:
#   -gameId: integer representation of the
#       desired game's ID number
# RETURNS:
#   -list of shifts, sorted by start time
def pullGameShifts(gameId):
    response = requests.get("https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId="+str(gameId))
    return cleanGameShifts(response.json()['data'])

def gameIsFinished(gameData):
    return gameData["gameState"] == "OFF"


#cleanGameShifts takes a list of game shifts
#   in the format given by the NHL's API, and cleans
#   the data to make it useable for this projects
#   purposes.
# PARAMETERS:
#   -gameShifts: list containing shift data
# RETURNS:
#   -list of shifts, sorted by start time
def cleanGameShifts(gameShifts):
    for shift in gameShifts:
        shift['endTime'] = convertTime(shift['endTime'])
        shift['startTime'] = convertTime(shift['startTime'])
    return sorted(gameShifts, key=lambda d: d['startTime'])


#convertTime takes a string representation of time
#   and converts it into a single integer, representing
#   time of game since opening faceoff of the period.
# PARAMETERS:
#   -timeStr: string representation of time of the period
# RETURNS:
#   -integer representation of seconds into period
def convertTime(timeStr):
    minutes = int(timeStr[0:2])
    seconds = int(timeStr[3:5])
    return minutes*60 + seconds


#getEventsList takes a diction of game data in the
#   format given by the NHL's API, cleans the data
#   to make it useable for this project.
# PARAMETERS:
#   -gameData: dictionary containing game data
# RETURNS:
#   -list of events, cleaned for use in this project
def getEventsList(gameData):
    events = cleanEvents(gameData['plays'])
    return events
    

#cleanEvents takes a dictionary of game events and
#   cleans the data to make it useable for this
#   projects purposes.
# PARAMETERS:
#   -gameEvents: list containing game event data
# RETURNS:
#   -list of cleaned events, sorted by start time
def cleanEvents(gameEvents):
    for event in gameEvents:
        event['timeInPeriod'] = convertTime(event['timeInPeriod'])
    return sorted(gameEvents, key=lambda d: d['timeInPeriod'])


#getPlayerList takes a dictionary of game data and
#   returns the dictionary of players in the game
# PARAMETERS:
#   -gameData: list containing game data
# RETURNS:
#   -dictionary of players
def getPlayerDict(gameData):
    playerDict = {}
    for player in gameData['rosterSpots']:
        playerDict[player['playerId']] = player

    return playerDict


#pullSeason does a get request on the NHL's API
#   to get season data, including a list of
#   games that happen within that season
# PARAMETERS:
#   -year: year of season to pull data from in YYYY format
# RETURNS:
#   -list of games that happen in that season
def pullSeason(year):
    date = datetime(year, 7,1)
    endDate = datetime(year+1,7,1)
    gameList = []
    while date < endDate:
        response = requests.get(NHL_STATS_API_URL+"/v1/schedule/"+date.strftime("%Y-%m-%d"))

        for day in response.json()['gameWeek']:
            for game in day['games']:
                if 'id' in game and isRegularSeasonGame(game['id']):
                    gameList.append(game['id'])

        # increment date for next loop
        if 'nextStartDate' in response.json():
            date = datetime.strptime(response.json()['nextStartDate'], "%Y-%m-%d")
        else:
            date += timedelta(days=7)

    return gameList

def pullTeamSeason(year, team):
    seasonCode = year*10000+year+1
    gameIdList = []
    response = requests.get("https://api-web.nhle.com/v1/club-schedule-season/"+team+"/"+str(seasonCode))
    for game in response.json()['games']:
        if game['gameType'] == 2:
            gameIdList.append(game['id'])

    return gameIdList

def isRegularSeasonGame(gameId):
    return (gameId//10000)%10 == 2

#processGame takes a gameId and uses it to pull
#   the gameData then process the resulting data
#   to give a stats overview for each player in
#   the game.
# PARAMETERS:
#   -gameId: id of game to process
# RETURNS:
#   -a dictionary of players statistics
def processGame(gameId):
    #pull necessary data
    gameData = pullGameData(gameId)
    gameShifts = pullGameShifts(gameId)
    players = getPlayerDict(gameData)
    gameEvents = getEventsList(gameData)
    gameStats = {}

    for event in gameEvents:
        playersOnIce = []
        for shift in gameShifts:
            if isEventDuringShift(event,shift):
                playersOnIce.append(players[shift['playerId']])
            elif shift['startTime'] > event['timeInPeriod']:
                break
        playersFor, playersAgainst = separatePlayersByTeam(playersOnIce,event)

        event['playersFor'] = playersFor
        event['playersAgainst'] = playersAgainst

        for player in playersOnIce:
            if str(player['playerId']) in gameStats:
                gameStats[str(player['playerId'])]['events'].append(event)
            else:
                gameStats[str(player['playerId'])] = { 'events': [ event ] }

    playerIDs = []
    for player in players:
        playerIDs.append(player)

    eventsByType = organizeGameEventsByType(gameEvents)

    #get goals and assists for gameStats
    points = processGoals(eventsByType['goals'],playerIDs)

    #get TOI for gameStats
    toi = processTOI(gameShifts,playerIDs)

    #get Shot Attempts
    shotStats = processShotAttempts(eventsByType['shotAttempts'], playerIDs)

    #get PIM for gameStats
    pim = processPenalty(eventsByType['penalties'],playerIDs)

    #get faceoffs for gameStats
    faceoffs = processFaceoff(eventsByType['faceoffs'], playerIDs)

    #combine stats into single dictionary of statistics by players
    for player in playerIDs:
        if str(player) in gameStats:
            #players who show up in playerIDs but not gameStats
            #   are players who dressed but did not play
            gameStats[str(player)]['gameId'] = gameData['id']
            gameStats[str(player)]['G'] = points[player]['G']
            gameStats[str(player)]['A'] = points[player]['A']
            gameStats[str(player)]['P'] = points[player]['P']
            gameStats[str(player)]['TOI'] = toi[player]
            gameStats[str(player)]['CF'] = shotStats[player]['CF']
            gameStats[str(player)]['CA'] = shotStats[player]['CA']
            gameStats[str(player)]['FF'] = shotStats[player]['FF']
            gameStats[str(player)]['FA'] = shotStats[player]['FA']
            gameStats[str(player)]['PIM'] = pim[player]
            gameStats[str(player)]['FOW'] = faceoffs[player]['FOW']
            gameStats[str(player)]['FOL'] = faceoffs[player]['FOL']

            if 'saves' in shotStats[player]:
                gameStats[str(player)]['saves'] = shotStats[player]['saves']
            if 'GA' in points[player]:
                gameStats[str(player)]['GA'] = points[player]['GA']

    gameData['playerGames'] = gameStats

    return gameData


#organizeGameEventsByType takes a list of game
#   events into lists of appropriate types.
#   Events will be organized into either goal,
#   shot attempt, penalty, or faceoff. 
# PARAMETERS:
#   -gameId: id of game to process
# RETURNS:
#   -a dictionary of players statistics
def organizeGameEventsByType(gameEvents):
    organizedEvents = {
        'goals': [],
        'shotAttempts': [],
        'penalties': [],
        'faceoffs': []
    }

    for event in gameEvents:
        if event['typeCode'] == 502:
            # faceoff event
            organizedEvents['faceoffs'].append(event)
        elif event['typeCode'] == 509:
            # penalty event
            organizedEvents['penalties'].append(event)
        elif event['typeCode'] == 506:
            # shot on goal event
            organizedEvents['shotAttempts'].append(event)
        elif event['typeCode'] == 508:
            # blocked shot event
            organizedEvents['shotAttempts'].append(event)
        elif event['typeCode'] == 507:
            # missed shot event
            organizedEvents['shotAttempts'].append(event)
        elif event['typeCode'] == 505:
            # goal event
            organizedEvents['goals'].append(event)
            organizedEvents['shotAttempts'].append(event)
 
    return organizedEvents


#processShotAttempts takes a list of gameEvents and 
#   processes it to find the corsi stats for
#   each player in the game. Corsi is measured
#   as (Shots on Goal + Shots Blocked + Shots
#   Missed), creating a sum of all shot attempts
#   separated by team, so each player will have
#   Corsi FOR, which covers all shot attempts for
#   that player's team while that player is on the
#   ice, and Corsi AGAINST, which covers all shot
#   attempts for the shot attempts against a 
#   player's team while that player is on the ice.
#   Fenwick is similar, but does not include blocked
#   shots, because blocked shots can be considered
#   less dangerous shot attempts.
# PARAMETERS:
#   -shotEvents: a list of shot attempts that happen during
#       the game, including players on the ice at the
#       time of the event
#   -players: list of all player ID's who play in the game
# RETURNS:
#   -a dictionary of players Shot Attempt Stats
def processShotAttempts(shotEvents, players):
    playerStats = {}
    for player in players:
        playerStats[player] = {
            'CF' : 0,
            'CA' : 0,
            'FF' : 0,
            'FA' : 0
        }

    for event in shotEvents:
        # all shot attempt events are Corsi events
        for player in event['playersFor']:
            playerStats[player]['CF'] += 1

        for player in event['playersAgainst']:
            playerStats[player]['CA'] += 1

        # blocked shots are not Fenwick events, so check for
        #   blocked shots before adding Fenwick
        if event['typeCode'] != 508:
            for player in event['playersFor']:
                playerStats[player]['FF'] += 1

            for player in event['playersAgainst']:
                playerStats[player]['FA'] += 1

        # for shots on goal, add a save to goalie's stats
        if event['typeCode'] == 506:
            if 'saves' in playerStats[event['details']['goalieInNetId']]:
                playerStats[event['details']['goalieInNetId']]['saves'] += 1
            else:
                playerStats[event['details']['goalieInNetId']]['saves'] = 1
    

    return playerStats


#processTOI takes gameShifts and a list of players
#   to find the total time on ice for each player
#   in the game.
# PARAMETERS:
#   -gameShifts: list of all shifts for each player
#       in the game
#   -players: list of all player ID's to play in the game
# RETURNS:
#   -a dictionary of player's TOI
def processTOI(gameShifts, players):
    toi = {}
    for player in players:
        toi[player] = 0

    for shift in gameShifts:
        toi[shift['playerId']] += shift['endTime'] - shift['startTime']

    return toi


#processPenalty takes gameEvents and a list of players
#   to find the number of penalty minutes each player
#   in the game gets
# PARAMETERS:
#   -penaltyEvents: list of all penalty events in the game
#   -players: list of all player ID's to play in the game
# RETURNS:
#   -a dictionary of player's penalty statistics
def processPenalty(penaltyEvents, players):
    penaltyStats = {}

    for player in players:
        penaltyStats[player] = 0

    for event in penaltyEvents:
        if 'committedByPlayerId' in event['details']:
            player = event['details']['committedByPlayerId']
            duration = event['details']['duration']
            penaltyStats[player] += duration

    return penaltyStats


#processFaceoff takes faceoffEvents and a list of players
#   to find the number of faceoff wins and losses for each
#   player in the game.
# PARAMETERS:
#   -faceoffEvents: list of all faceoff events in the game
#   -players: list of all player ID's to play in the game
# RETURNS:
#   -a dictionary of player's faceoff statistics
def processFaceoff(faceoffEvents, players):
    faceoffStats = {}

    for player in players:
        faceoffStats[player] = {
            'FOW': 0,
            'FOL': 0
        }
    
    for event in faceoffEvents:
        wPlayer = event['details']['winningPlayerId']
        lPlayer = event['details']['losingPlayerId']
        faceoffStats[wPlayer]['FOW'] += 1
        faceoffStats[lPlayer]['FOL'] += 1

    return faceoffStats


#processGoals takes goalEvents and a list of players
#   to find the number of goals and assists for each
#   player in the game.
# PARAMETERS:
#   -goalEvents: list of all goal events in the game
#   -players: list of all player ID's to play in the game
# RETURNS:
#   -a dictionary of player's goal and assist statistics
def processGoals(goalEvents, players):
    goalStats = {}

    for player in players:
        goalStats[player] = {
            'G': 0,
            'A': 0,
            'P': 0
        }

    for event in goalEvents:
        goalScorer = event['details']['scoringPlayerId']
        goalStats[goalScorer]['G'] += 1
        goalStats[goalScorer]['P'] += 1

        #goals can be unassisted, so check to make sure assist1PlayerId exists
        if 'assist1PlayerId' in event['details']:
            firstAssist = event['details']['assist1PlayerId']
            goalStats[firstAssist]['A'] += 1
            goalStats[firstAssist]['P'] += 1
        if 'assist2PlayerId' in event['details']:
            secondAssist = event['details']['assist2PlayerId']
            goalStats[secondAssist]['A'] += 1
            goalStats[secondAssist]['P'] += 1

        if 'goalieInNetId' in event['details'] and 'GA' in goalStats[event['details']['goalieInNetId']]:
            goalStats[event['details']['goalieInNetId']]['GA'] += 1
        elif 'goalieInNetId' in event['details']:
            goalStats[event['details']['goalieInNetId']]['GA'] = 1

    return goalStats

        

#separatePlayersByTeam takes a game event and a
#   list of players on the ice for said event and
#   separates the players into two lists, one for
#   players who were on the team the event benefits
#   and one for players who were on the team the
#   event went against.
# PARAMETERS:
#   -players: list of player ID's for players on the ice
#   -event: event that happened during shift
# RETURNS:
#   -two lists, first list is the list of players
#       on the event FOR team, and second list is
#       players on the event AGAINST team. Returns
#       [],[] if assigning FOR/AGAINST is N/A
def separatePlayersByTeam(players,event):    
    playersFor = []
    playersAgainst = []

    if (not 'details' in event or not 'eventOwnerTeamId' in event['details']):
        return playersFor,playersAgainst

    for player in players:
        if player['teamId'] == event['details']['eventOwnerTeamId']:
            playersFor.append(player['playerId'])
        else:
            playersAgainst.append(player['playerId'])

    return playersFor,playersAgainst
    

#isEventDuringShift takes an event and shift to 
#   determine if the event happened during a player's
#   shift.
# PARAMETERS:
#   -event: dict of event data
#   -shift: dict of shift data
# RETURNS:
#   -boolean, true if the event happens during shift,
#       false if the event does not happen during shift
def isEventDuringShift(event,shift):
    return (shift['startTime'] <= event['timeInPeriod'] and shift['endTime'] > event['timeInPeriod'] and shift['period'] == event['periodDescriptor']['number'])


#processSeason takes a year, pulls that season's
#   data, then processes the season game by game
#   to get cumulative stats for each player in the
#   NHL
# PARAMETERS:
#   -year - year of season to process in YYYY format
# RETURNS:
#   -dictionary of player statistics
def processSeason(year):
    gameList = pullSeason(year)

    gameStats = {}

    for game in gameList:
        print("Processing game "+ str(game) +"...")
        gameStats[game] = processGame(game)
        print(gameStats[game])

    seasonStats = {}

    return seasonStats


if __name__ == "__main__":
    main()