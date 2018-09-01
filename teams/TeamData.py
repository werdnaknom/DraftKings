import nflgame as nfl
import csv
import datetime

import pandas as pd
import numpy as np

class ExtractGameData():
    def openWriter(self, output_file):
        csvfile = open(output_file, 'w', newline="")
        writer = csv.writer(csvfile, delimiter=",")
        self.writer = writer

    def writeHeader(self):
        self.writer.writerow(['gameKey', 'season', 'day', 'month', 'time', 'weekDay',
                              'week', 'year', 'home', 'away', 'scoreHome',
                              'scoreAway', 'homeFirstDowns', 'homeTotalYards', 'homePassingYards',
                              'homeRushingYards', 'homePenaltyCount',
                              'homePenaltyYards', 'homeTurnovers', 'homePuntCount',
                              'homePuntYards',
                              'homePuntAvg', 'homePossessionTime',
                              'awayFirstDowns', 'awayTotalYards', 'awayPassingYards',
                              'awayRushingYards', 'awayPenaltyCount',
                              'awayPenaltyYards', 'awayTurnovers', 'awayPuntYards',
                              'awayPuntAvg', 'awayPossessionTime'
                              ])

    def getGames(self, year):
        return nfl.games(year)

    def writeGameStats(self, game):
        gamestats = self._getGameStats(game)
        home_stats = self._getTeamStats(game.stats_home)
        away_stats = self._getTeamStats(game.stats_away)
        stats = gamestats + home_stats + away_stats
        #print(stats)
        self.writer.writerow(stats)
        #self._writeTeamStats(game.gamekey, game.schedule, game.home, game.away, game.score_home, game.score_away, game.stats_home, game.stats_away)

    def _getGameStats(self, game):
        gamestats = [game.gamekey,
                     game.schedule['season_type'],
                     game.schedule['day'],
                     game.schedule['month'],
                     game.schedule['time'],
                     game.schedule['wday'],
                     game.schedule['week'],
                     game.schedule['year'],
                     game.schedule['home'],
                     game.schedule['away'],
                     game.score_home,
                     game.score_away]
        return gamestats

    def _getTeamStats(self, stats):
        teamstats = [stats.first_downs,
               stats.total_yds,
               stats.passing_yds,
               stats.rushing_yds,
               stats.penalty_cnt,
               stats.penalty_yds,
               stats.turnovers,
               stats.punt_cnt,
               stats.punt_yds,
               stats.punt_avg,
               self.__getSecondsDelta(stats.pos_time.clock)]
        return teamstats

    def __getSecondsDelta(self, time):
        minutes, seconds = [int(x) for x in time.split(':')]
        x = datetime.timedelta(minutes=minutes, seconds=seconds)
        return x.seconds

    def extractGames(self):
        self.openWriter("games.csv")
        self.writeHeader()

        current_year, current_week = nfl.live.current_year_and_week()
        for year in range(2009, current_year + 1):
            games = nfl.games(year)
            for game in games:
                self.writeGameStats(game)




class extractTeamGameData(object):

    def __init__(self, input_file, output_file):
        self.input = input_file
        self.output = output_file

    def openWriter(self):
        csvfile = open(self.output, 'w', newline="")
        writer = csv.writer(csvfile, delimiter=",")
        self.writer = writer

    def _openInput(self):
        csvfile = pd.read_csv(self.input, index_col=False)
        return csvfile

    def _updateELO(self, teamELO, opptELO, pointDiff, home=True):
        # https://fivethirtyeight.com/features/introducing-nfl-elo-ratings/
        K = 20
        homeAdvantage = 65
        if home:
            teamELO += homeAdvantage
        else:
            opptELO += homeAdvantage

        if pointDiff >= 0:
            mov = self.__marginOfVictory(loserELO = opptELO, winnerELO = teamELO,
                                         pointDiff = pointDiff)
        else:
            mov = self.__marginOfVictory(loserELO=teamELO, winnerELO=opptELO,
                                         pointDiff=pointDiff)
        mov += 1
        updateELO = np.log([mov])[0] * K

        #print(mov, updateELO)
        return round(updateELO)

    def __marginOfVictory(self, winnerELO, loserELO, pointDiff):
        absPD = np.abs([pointDiff])
        mov = np.log([absPD + 1]) * 2.2/((winnerELO - loserELO) *.001 +2.2)
        return mov[0][0]

    def _yearlyReadjust(self, score, mean):
        readjust = (score - mean)/2.0
        score -= round(readjust)
        return score

    def checkYear(self, year):
        if self.__getYear() != year:
            self.__setYear(year)
            return True
        else:
            return False

    def __setYear(self, year):
        self.year = year

    def __getYear(self):
        return self.year

    def __getDefaults(self):
        teamScore = {
            'TEN': 1300, 'MIA': 1300, 'KC': 1300,
            'PHI': 1300, 'DEN': 1300, 'MIN': 1300,
            'NYJ': 1300, 'JAC': 1300, 'DET': 1300,
            'DAL': 1300, 'SF': 1300, 'WAS': 1300,
            'STL': 1300, 'CHI': 1300, 'BUF': 1300,
            'SD': 1300, 'CAR': 1300, 'CIN': 1300,
            'ARI': 1300, 'OAK': 1300, 'NE': 1300,
            'NO': 1300, 'HOU': 1300, 'TB': 1300,
            'SEA': 1300, 'PIT': 1300, 'CLE': 1300,
            'BAL': 1300, 'NYG': 1300, 'IND': 1300,
            'ATL': 1300, 'GB': 1300, 'LA': 1300,
            'JAX': 1300, 'LAC': 1300
        }

        offensiveScore = dict.fromkeys(teamScore, 300)
        defensiveScore = dict.fromkeys(teamScore, 300)
        passAvg = dict.fromkeys(teamScore, 0)
        runAvg = dict.fromkeys(teamScore, 0)
        runDef = dict.fromkeys(teamScore, 0)
        passDef = dict.fromkeys(teamScore, 0)
        totalYds = dict.fromkeys(teamScore, 0)
        scoreAvg = dict.fromkeys(teamScore, 0)

        return teamScore, offensiveScore, defensiveScore, passAvg, runAvg,\
               passDef, runDef, totalYds, scoreAvg

    def updateTeamScore(self, teamDict, gameRow):
        score = 0
        return score

    def average(self, teamDict, gameRow, stat, home=True):
        if home and stat == "rush":
            data = [teamDict[gameRow.home], gameRow.homeRushingYards]
        elif home and stat == "pass":
            data = [teamDict[gameRow.home], gameRow.homePassingYards]
        elif home and stat == "total":
            data = [teamDict[gameRow.home], gameRow.homeTotalYards]
        elif home and stat == "score":
            data = [teamDict[gameRow.home], gameRow.scoreHome]
        elif not home and stat == "rush":
            data = [teamDict[gameRow.away], gameRow.awayRushingYards]
        elif not home and stat == "pass":
            data = [teamDict[gameRow.away], gameRow.awayPassingYards]
        elif not home and stat == "total":
            data = [teamDict[gameRow.away], gameRow.awayTotalYards]
        elif not home and stat == "score":
            data = [teamDict[gameRow.away], gameRow.scoreAway]
        else:
            raise("Not an Average! %s, home=%s" % (stat, home))
        #print(data)
        return int(np.average(data))

    def __winning(self, points, pointsAgainst):
        if points == pointsAgainst:
            return 0
        elif points > pointsAgainst:
            return 1
        else:
            return -1

    def _createSeries(self, gameRow, scores, home=True):
        self._updateELO(scores['teamScore'], scores['opptTeamScore'],
                        gameRow.scoreHome - gameRow.scoreAway)
        if home:
            temp_ser = pd.Series({
                'team': gameRow.home, 'gameKey' : str(gameRow.gameKey),'home' : home,
                'offenseScore' : scores['offenseScore'],
                'defenseScore' : scores['defenseScore'],
                'teamScore' : scores['teamScore'],
                'rushAvg': scores['rushAvg'],
                'passAvg': scores['passAvg'],
                'totalAvg': scores['totalAvg'],
                'scoreAvg': scores['scoreAvg'],
                'opptOffenseScore' : scores['opptOffenseScore'],
                'opptDefenseScore' : scores['opptDefenseScore'],
                'opptTeamScore' : scores['opptTeamScore'],
                'opptRushAvg' : scores['opptRushAvg'],
                'opptPassAvg' : scores['opptPassAvg'],
                'opptTotalAvg': scores['opptTotalAvg'],
                'opptScoreAvg': scores['opptScoreAvg'],
                'points' : gameRow.scoreHome,
                'pointsAgainst' : gameRow.scoreAway,
                'win' : self.__winning(gameRow.scoreHome, gameRow.scoreAway),
                'year': str(gameRow.year), 'week': str(gameRow.week),
                'firstDowns': gameRow.homeFirstDowns,
                'totalYards' : gameRow.homeTotalYards,
                'passYards' : gameRow.homePassingYards,
                'rushYards' : gameRow.homeRushingYards,
                'penaltyCount' : gameRow.homePenaltyCount,
                'penaltyYards' : gameRow.homePenaltyYards,
                'turnovers' : gameRow.homeTurnovers,
                'possessionTime' : gameRow.homePossessionTime,
                'opptFirstDowns': gameRow.awayFirstDowns,
                'opptTotalYards': gameRow.awayTotalYards,
                'opptPassYards': gameRow.awayPassingYards,
                'opptRushYards': gameRow.awayRushingYards,
                'opptPenaltyCount': gameRow.awayPenaltyCount,
                'opptPenaltyYards': gameRow.awayPenaltyYards,
                'opptTurnovers': gameRow.awayTurnovers,
                'opptPossessionTime': gameRow.awayPossessionTime,
            })
        else:


            temp_ser = pd.Series({
                'team': gameRow.away, 'gameKey' : gameRow.gameKey,'home' : home,
                'offenseScore' : scores['offenseScore'],
                'defenseScore' : scores['defenseScore'],
                'teamScore' : scores['teamScore'],
                'rushAvg': scores['rushAvg'],
                'passAvg': scores['passAvg'],
                'totalAvg': scores['totalAvg'],
                'scoreAvg': scores['scoreAvg'],
                'opptOffenseScore' : scores['opptOffenseScore'],
                'opptDefenseScore' : scores['opptDefenseScore'],
                'opptTeamScore' : scores['opptTeamScore'],
                'opptRushAvg' : scores['opptRushAvg'],
                'opptPassAvg' : scores['opptPassAvg'],
                'opptTotalAvg': scores['opptTotalAvg'],
                'opptScoreAvg': scores['opptScoreAvg'],
                'points' : gameRow.scoreAway,
                'pointsAgainst' : gameRow.scoreHome,
                'win' : self.__winning(gameRow.scoreAway, gameRow.scoreHome),
                'year': gameRow.year, 'week': gameRow.week,
                'firstDowns': gameRow.awayFirstDowns,
                'totalYards': gameRow.awayTotalYards,
                'passYards': gameRow.awayPassingYards,
                'rushYards': gameRow.awayRushingYards,
                'penaltyCount': gameRow.awayPenaltyCount,
                'penaltyYards': gameRow.awayPenaltyYards,
                'turnovers': gameRow.awayTurnovers,
                'possessionTime': gameRow.awayPossessionTime,
                'opptFirstDowns': gameRow.homeFirstDowns,
                'opptTotalYards': gameRow.homeTotalYards,
                'opptPassYards': gameRow.homePassingYards,
                'opptRushYards': gameRow.homeRushingYards,
                'opptPenaltyCount': gameRow.homePenaltyCount,
                'opptPenaltyYards': gameRow.homePenaltyYards,
                'opptTurnovers': gameRow.homeTurnovers,
                'opptPossessionTime': gameRow.homePossessionTime
            })

        return temp_ser

    def extractTeamData(self):
        team_df = pd.DataFrame(columns=['team', 'gameKey', 'home',
                                        'offenseScore', 'defenseScore', 'teamScore',
                                        'rushAvg', 'passAvg', 'totalAvg',
                                        'scoreAvg', 'opptOffenseScore',
                                        'opptDefenseScore',
                                        'opptTeamScore', 'opptRushAvg',
                                        'opptPassAvg', 'opptTotalAvg',
                                        'opptScoreAvg', 'points',
                                        'pointsAgainst', 'win', 'year', 'week'
                                        ]
                               )
        input_df = self._openInput()

        self.__setYear(2009)


        teamScore, offensiveScore, defensiveScore, passAvg, rushAvg,\
        runDef, passDef, totalAvg, scoreAvg = self.__getDefaults()

        for col, row in input_df.iterrows():
            if self.checkYear(row.year):
                print("Yearly Readjust!")
                for team in teamScore:
                    teamScore[team] = self._yearlyReadjust(teamScore[team], 1300)

            #HOME
            temp_ser = self._createSeries(gameRow=row,
                                          scores={'offenseScore' : offensiveScore[row.home],
                                                  'defenseScore' : defensiveScore[row.home],
                                                  'teamScore' : teamScore[row.home],
                                                  'rushAvg': rushAvg[row.home],
                                                  'passAvg': passAvg[row.home],
                                                  'totalAvg': totalAvg[row.home],
                                                  'scoreAvg': scoreAvg[row.home],
                                                  'opptOffenseScore' : offensiveScore[row.away],
                                                  'opptDefenseScore' : defensiveScore[row.away],
                                                  'opptTeamScore' : teamScore[row.away],
                                                  'opptRushAvg': rushAvg[row.away],
                                                  'opptPassAvg': passAvg[row.away],
                                                  'opptTotalAvg': totalAvg[row.away],
                                                  'opptScoreAvg': scoreAvg[row.away]
                                                  }
                                          )

            team_df = team_df.append(temp_ser, ignore_index=True)

            passAvg[row.home] = self.average(passAvg, row, stat="pass")
            rushAvg[row.home] = self.average(rushAvg, row, stat="rush")
            totalAvg[row.home] = self.average(totalAvg, row, stat="total")
            scoreAvg[row.home] = self.average(scoreAvg, row, stat="score")


            #AWAY
            temp_ser = self._createSeries(gameRow=row,
                                          scores={'offenseScore' : offensiveScore[row.away],
                                                  'defenseScore' : defensiveScore[row.away],
                                                  'teamScore' : teamScore[row.away],
                                                  'rushAvg': rushAvg[row.away],
                                                  'passAvg': passAvg[row.away],
                                                  'totalAvg': totalAvg[row.away],
                                                  'scoreAvg': scoreAvg[row.away],
                                                  'opptOffenseScore' : offensiveScore[row.home],
                                                  'opptDefenseScore' : defensiveScore[row.home],
                                                  'opptTeamScore' : teamScore[row.home],
                                                  'opptRushAvg': rushAvg[row.home],
                                                  'opptPassAvg': passAvg[row.home],
                                                  'opptTotalAvg': totalAvg[row.home],
                                                  'opptScoreAvg': scoreAvg[row.home]
                                                  },
                                          home=False)
            team_df = team_df.append(temp_ser, ignore_index=True)

            passAvg[row.away] = self.average(passAvg, row, stat="pass", home=False)
            rushAvg[row.away] = self.average(rushAvg, row, stat="rush", home=False)
            totalAvg[row.away] = self.average(totalAvg, row, stat="total", home=False)
            scoreAvg[row.away] = self.average(scoreAvg, row, stat="score", home=False)

            eloUpdate = self._updateELO(teamScore[row.home],
                                        teamScore[row.away],
                                        row.scoreHome - row.scoreAway)
            if row.scoreHome >= row.scoreAway:
                teamScore[row.home] += eloUpdate
                teamScore[row.away] -= eloUpdate
            else:
                teamScore[row.home] -= eloUpdate
                teamScore[row.away] += eloUpdate

        print(team_df.tail(4))
        print(team_df.describe())
        team_df.to_csv('teams.csv')


if __name__ == "__main__":
    update = False
    if update:
        ext = ExtractGameData()
        ext.extractGames()

    ext_team = extractTeamGameData(input_file='games.csv', output_file='teams.csv')
    ext_team.extractTeamData()


    #teams.writeGameData(game.home, game.away, game.score_home, game.score_away, game.stats_home, game.stats_away)
    #print(r)
    #print(game.away)
    #print(game.home)
    #print(game.score_away)
    #print(game.score_home)
    #print(game.away)
    #print(game.stats_away._fields)
    #print(game.stats_away)
    #print(game.stats_away.pos_time)
