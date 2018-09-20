import urllib.request
import base64
import datetime
import json
import sys

emojis = {}
emojis["ARI"] = "<:ARI:269315353153110016>"
emojis["ANA"] = "<:ANA:271881573375279104>"
emojis["BOS"] = "<:BOS:269315305707143168>"
emojis["BUF"] = "<:BUF:269315526717603840>"
emojis["CGY"] = "<:CGY:269315410375999509>"
emojis["CAR"] = "<:CAR:269315433595666432>"
emojis["CHI"] = "<:CHI:269315278880505857>"
emojis["COL"] = "<:COL:269315269002919946>"
emojis["CBJ"] = "<:CBJ:269315288988647425>"
emojis["DAL"] = "<:DAL:269315550188929024>"
emojis["DET"] = "<:DET:269315577682722826>"
emojis["EDM"] = "<:EDM:269315479464706048>"
emojis["FLA"] = "<:FLO:269315494652280832>"
emojis["FLO"] = "<:FLO:269315494652280832>"
emojis["LAK"] = "<:LAK:269315457188626432>"
emojis["MIN"] = "<:MIN:269315563606507521>"
emojis["MTL"] = "<:MTL:269315427874635776>"
emojis["NSH"] = "<:NSH:269315511702126594>"
emojis["NJD"] = "<:NJD:269315361126481930>"
emojis["NYI"] = "<:NYI:269315441204264960>"
emojis["NYR"] = "<:NYR:269315518907809792>"
emojis["OTT"] = "<:OTT:269315534301036544>"
emojis["PHI"] = "<:PHI:269315418513080331>"
emojis["PIT"] = "<:PIT:269315504324214786>"
emojis["STL"] = "<:STL:269315296328679436>"
emojis["SJS"] = "<:SJS:269315542509289472>"
emojis["TBL"] = "<:TBL:269315471919022090>"
emojis["TOR"] = "<:TOR:269315465069723648>"
emojis["VAN"] = "<:VAN:269315315194658818>"
emojis["VGK"] = "<:VGK:363836502859448320>"
emojis["WSH"] = "<:WSH:269327070977458181>"
emojis["WPG"] = "<:WPJ:269315448833703946>"
emojis["WPJ"] = "<:WPJ:269315448833703946>"

started = []
completed = []
reported = {}
lastDate = None
messages = {}

# Gets the feed using the new NHL.com API
def getFeed(url):
	request = urllib.request.Request(url)
	response = urllib.request.urlopen(request)
	return json.loads(response.read().decode())

def parseGame(game):
	global started, reported, completed, messages

	stringsToAnnounce = []
	stringsToEdit = {}

	playbyplayURL = "https://statsapi.web.nhl.com" + game["link"]
	try:
		playbyplay = getFeed(playbyplayURL)
	except Exception as e:
		print("Failed to find feed.")
		return [], {}

	away = playbyplay["gameData"]["teams"]["away"]["abbreviation"]
	home = playbyplay["gameData"]["teams"]["home"]["abbreviation"]
	key = away + "-" + home

	isFinal = playbyplay["gameData"]["status"]["detailedState"] == "Final"
	isInProgress = playbyplay["gameData"]["status"]["detailedState"] == "In Progress"

	if isInProgress and key not in started:
		stringsToAnnounce.append((None, emojis[away] + " " + away + " at " + emojis[home] + " " + home + " Starting."))
		started.append(key)

	# check to see if score is different from what we have saved
	goals = playbyplay["liveData"]["plays"]["scoringPlays"]

	for goalindex in range(0, len(goals)):
		goal = goals[goalindex]
		gamekey = game["gamePk"]
		if gamekey not in reported:
			reported[gamekey] = []

		awayScore = playbyplay["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["goals"]
		homeScore = playbyplay["liveData"]["boxscore"]["teams"]["home"]["teamStats"]["teamSkaterStats"]["goals"]
		score = "(" + away + " " + str(awayScore) + ", " + home + " " + str(homeScore) + ")"

		while len(reported[gamekey]) > len(goals):
			stringsToAnnounce.append((None, "Last goal in " + emojis[away] + " " + away + "-" + emojis[home] + " " + home + " disallowed (beta feature, report to SPRX97 if incorrect)."))
			gamegoalkey = str(gamekey) + ":" + str(reported[gamekey].pop())
			msg = messages[gamegoalkey]
			stringsToEdit[msg[2]] = "~~" + msg[0] + "~~ " + score
			
		goalkey = playbyplay["liveData"]["plays"]["allPlays"][goal]["about"]["eventId"]
		goal = playbyplay["liveData"]["plays"]["allPlays"][goal]
		gamegoalkey = str(gamekey) + ":" + str(goalkey)

		strength = "(" + goal["result"]["strength"]["code"] + ") "
		if strength == "(EVEN) ":
			strength = ""
		en = ""
		if "emptyNet" in goal["result"] and goal["result"]["emptyNet"]:
			en = "(EN) "

		team = emojis[goal["team"]["triCode"]] + " " + goal["team"]["triCode"]
		period = "(" + goal["about"]["ordinalNum"] + ")"
		time = goal["about"]["periodTime"] + " " + goal["about"]["ordinalNum"]
				
		goalstr = "GOAL " + strength + en + team + " " + time + ": " + goal["result"]["description"]
		if gamegoalkey not in messages:
			stringsToAnnounce.append((gamegoalkey, goalstr + " " + score))
			messages[gamegoalkey] = [goalstr, score, None]
			reported[gamekey].append(goalkey)
		elif messages[gamegoalkey][0] != goalstr: # update a previously posted goal
			stringsToEdit[messages[gamegoalkey][2]] = goalstr + " " + messages[gamegoalkey][1]
			messages[gamegoalkey][0] = goalstr

	# print final result
	if isFinal and key not in completed:
		if playbyplay["liveData"]["plays"]["allPlays"][-1]["result"]["eventTypeId"] == "GAME_END":
			awayScore = playbyplay["liveData"]["plays"]["allPlays"][-1]["about"]["goals"]["away"]
			homeScore = playbyplay["liveData"]["plays"]["allPlays"][-1]["about"]["goals"]["home"]

			skip = False
			if awayScore == homeScore: # adjust for shootout winner
				if playbyplay["liveData"]["linescore"]["shootoutInfo"]["away"]["scores"] > playbyplay["liveData"]["linescore"]["shootoutInfo"]["home"]["scores"]:
					awayScore += 1
				elif playbyplay["liveData"]["linescore"]["shootoutInfo"]["away"]["scores"] < playbyplay["liveData"]["linescore"]["shootoutInfo"]["home"]["scores"]:
					homeScore += 1
				else:
					skip = True
			if not skip:
				period = "(" + playbyplay["liveData"]["plays"]["allPlays"][-1]["about"]["ordinalNum"] + ")"
				if period == "(3rd)":
					period = ""
				finalstring = emojis[away] + " " + away + " " + str(awayScore) + ", " + emojis[home] + " " + home + " " + str(homeScore) + " Final " + period
				stringsToAnnounce.append((None, finalstring))
				completed.append(key)
	return stringsToAnnounce, stringsToEdit


# parses the NHL scoreboard for a given date
def parseScoreboard(date): # YYYY-mm-dd format
	global lastDate

	# reseet for new day
	if date != lastDate:
		reported = {}
		started = []
		completed = []
		lastDate = date
		messages = {}

	try:
		root = getFeed("https://statsapi.web.nhl.com/api/v1/schedule?startDate=" + date + "&endDate=" + date + "&expand=schedule.linescore")
	except Exception as e:
		print("Failed to find feed.")
		return [], {}

	stringsToAnnounce = []
	stringsToEdit = {}

	games = root["dates"][0]["games"]
	for game in games:
		ann, edit = parseGame(game)
		stringsToAnnounce.extend(ann)
		stringsToEdit.update(edit)
	return stringsToAnnounce, stringsToEdit

if __name__ == "__main__":
	date = (datetime.datetime.now()-datetime.timedelta(hours=6)).strftime("%Y-%m-%d")
	for (k, s) in parseScoreboard(date)[0]:
		print(k, s)
