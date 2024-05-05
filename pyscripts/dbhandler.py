from pymongo import MongoClient
import nhlapihandler
from dotenv import load_dotenv
import os
import sys

def main():
    #updateGame(2023020204)
    # client = get_client()
    # updateSeason(2023,client)
    # client.close()

    if len(sys.argv) <= 2:
        print("Invalid syntax. Please use \"python3 dbhandler.py [functionName] [functionParameters]")
        print("Functions available: ")
        print("\tupdateGame")
        print("\t\tParameters -> gameId")
        print("\tupdatePlayers")
        print("\t\tParameters -> gameId")
        print("\tupdatePlayerSeason")
        print("\t\tParameters -> playerId, year")
        print("\tupdateSeason")
        print("\t\tParameters -> year")
        return
    
    client = get_client()
    if sys.argv[1] == "updateGame":
        updateGame(int(sys.argv[2]),client)
    elif sys.argv[1] == "updatePlayers":
        updatePlayers(int(sys.argv[2]),client)
    elif sys.argv[1] == "updatePlayerSeason":
        updatePlayerSeason(int(sys.argv[2]),int(sys.argv[3]),client)
    elif sys.argv[1] == "updateSeason":
        updateSeason(int(sys.argv[2]),client)
    else:
        print("Invalid function Name")

    client.close()

def get_client():
    load_dotenv()
    DB_URL = os.getenv('DB_URL')
    client = MongoClient(DB_URL)
    return client

# updateGame pulls one game and processes it
#   to update the game and playerGame's in db
# PARAMATERS:
#   -gameId: int id of game needed to update
# RETURNS:
#   -nothing, but sends the game data to db
def updateGame(gameId,mongoClient):
    gameData = nhlapihandler.processGame(gameId)

    updatePlayers(gameData,mongoClient)

    db = mongoClient.test
    dbgames = db.games
    dbplayerGames = db.playerGames

    dbgame = dbgames.find_one( {'id': gameData['id']} )
    players = db.players.find() #list of all players

    if dbgame is not None:
        #print("Found Game")
        replace_result = dbgames.replace_one( 
            {'id': gameData['id']}, gameData
        )
        #print(replace_result)
        for player in gameData['playerGames']:
            for avsPlayer in players:
                if player['playerId'] == avsPlayer['playerId']:
                    replace_result = dbplayerGames.replace_one(
                        {'playerId': player}, gameData['playerGames']
                    )
                #print(replace_result)
    else:
        #print("No game")
        insert_result = dbgames.insert_one(gameData)
        #print(insert_result)
        for player in gameData['playerGames']:
            for avsPlayer in players:
                if player == avsPlayer['playerId']:
                    gameData['playerGames'][str(player)]['playerId'] = player
                    insert_result = dbplayerGames.insert_one(gameData['playerGames'][str(player)])
                    #print(insert_result)



# updatePlayers takes gameData and iterates through
#   the player list, searching for any players that
#   played in the game but are not in the db's player
#   collection, then adds those players.
# PARAMETERS:
#   -gameData: processed game data from the nhlapihandler
# RETURNS:
#   -nothing, but makes sure all players in a game are
#       present in the db 
def updatePlayers(gameData,mongoClient):
    db = mongoClient.test
    dbplayers = db.players

    for player in gameData['rosterSpots']:
        find_result = dbplayers.find_one( { 'playerId': player['playerId'] } )
        if find_result is None and player['teamId'] == 21: 
            insert_result = dbplayers.insert_one(player)
            #print(insert_result)

    



# updatePlayerSeason takes a playerId and calculates
#   the players cumulative season stats from the
#   playerGame collection.
# PARAMETERS:
#   -playerId: id number for player to update
#   -year: year to update in YYYY format
# RETURNS:
#   -nothing, but sends playerSeason data to db
def updatePlayerSeason(playerId,year,mongoClient):
    db = mongoClient.test
    #print("Updating player season " + str(playerId))
    #season codes are represented as YYYYyyyy
    #   where YYYY is the year passed to the function
    #   and yyyy is the next year, for example if
    #   YYYY = 2023, yyyy = 2024 and the code is
    #   20232024
    seasonCode = year *10000 + year + 1
    games = db.games.find( { 'season': seasonCode } )
    #print("Checking " + len(games)+ " games")
    seasonStats = emptySeasonStats(playerId)
    seasonStats['year'] = year
    if not games:
        return

    for game in games:
        #print("Checking Game " + game['id'])
        if str(playerId) in game['playerGames']:
            #print("Appears in Game " + game['id'])
            seasonStats = addGameToSeasonStats(seasonStats,game['playerGames'][str(playerId)],game)
    
    db.playerseasons.insert_one(seasonStats)



def addGameToSeasonStats(seasonStats,gameStats,gameData):
    for stat in seasonStats:
        if stat != 'playerId' and stat != 'gamesPlayed' and stat != 'year':
            seasonStats[stat] += gameStats[stat]
        elif stat == 'gamesPlayed':
            reducedGame = reduceGame(gameData)
            reducedGame['playerStats'] = gameStats
            del reducedGame['playerStats']['events']
            seasonStats[stat].append(reducedGame)

    return seasonStats


def reduceGame(gameData):
    reducedGame = {}
    reducedGame['id'] = gameData['id']
    reducedGame['homeTeam'] = gameData['homeTeam']
    reducedGame['awayTeam'] = gameData['awayTeam']
    reducedGame['gameType'] = gameData['gameType']
    reducedGame['date'] = gameData['gameDate']
    reducedGame['gameOutcome'] = gameData['gameOutcome']
    reducedGame['finalScore'] = gameData['summary']['linescore']['totals']

    return reducedGame


def emptySeasonStats(playerId):
    seasonStats = {
        'playerId': playerId,
        'G': 0,
        'A': 0,
        'P': 0,
        'TOI': 0,
        'CF': 0,
        'CA': 0,
        'FF': 0,
        'FA': 0,
        'PIM': 0,
        'FOW': 0,
        'FOL': 0,
        'gamesPlayed': []
    }
    return seasonStats

# updateSeason takes a year and updates the full
#   season's information for the full year, 
#   including updating each playerSeason
# PARAMETERS:
#   -year: year to update in YYYY format
# RETURNS:
#   -nothing, but makes updates to db
def updateSeason(year,mongoClient):
    #print("Pulling season games...")
    gameList = nhlapihandler.pullTeamSeason(year,'COL')
    #print("Season pulled successfully.")

    for game in gameList:
        #print("Updating game: " + str(game))
        updateGame(game, mongoClient)

    dbplayers = mongoClient.test.players

    playerList = dbplayers.find()

    for player in playerList:
        updatePlayerSeason(player['playerId'],year,mongoClient)



if __name__ == "__main__":
    main()