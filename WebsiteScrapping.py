import requests
import re

import json
from lxml import html
from lxml.etree import tostring
from bs4 import BeautifulSoup

import csv

import pandas as pd
import numpy as np

import nflgame as nfl

import os

class FootballWebsiteScraping():

    def __init__(self, url):
        self.url = url

    def getWeek(self):
        year, current_week = nfl.live.current_year_and_week()
        return year, current_week

    def getWebsite(self, year, week, position, leagueID):
        params = dict(season = year,
                      GameWeek = week,
                      PosID = self.getPosition(position),
                      leagueID = self.getLeague(leagueID))
        resp = requests.get(self.url, params=params)
        return resp

class CBS(FootballWebsiteScraping):

    def __init__(self,url='https://www.cbssports.com/fantasy/football/stats/sortable/points/' ):
        self.url = url

    def getURL(self):
        return self.url

    def setURL(self, year, position, league):
        url = 'https://www.cbssports.com/fantasy/football/stats/sortable/points/%s/%s/projections/%s/tp?&print_rows=9999' % (position, league, year)
        self.url = url

    def getWebsite(self, year, week, position='QB', league='ppr'):
        self.setURL(year, position, league)
        resp = requests.get(self.getURL())
        return resp

    def getPlayerAttributes(self, attr):

        name, team = attr.split(",")
        #print(attr, "Name:%s, Team:%s, Position:%s" % (name.strip(), team.strip(), position.strip()))
        return name.strip(), team.strip()

    def writeResults(self, output_file):
        with open(output_file, 'w', newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow(['Player', 'Position', 'Team', 'Opponent', 'CBS_FantasyPoints'])
            year, current_week = self.getWeek()
            for position in ['QB', 'RB', 'WR', 'K', 'TE', 'DST']:
                resp = self.getWebsite(year, current_week, position, league='ppr')
                soup = BeautifulSoup(resp.text, 'html.parser')
                tables = soup.findAll('table')
                player_table = tables[0]

                rows = player_table.findAll('tr')

                data = []

                for row in rows:
                    cols = row.findAll('td')
                    cols = [ele.text.strip() for ele in cols]
                    data.append([ele for ele in cols if ele])  # get rid of empty values
                for d in data[3:-1]:
                    name, team = self.getPlayerAttributes(d[0])
                    opponent = None
                    fantasy_prediction = d[-1:][0]
                    try:
                        writer.writerow([name, position, team, opponent, fantasy_prediction])
                    except:
                        print(d)

class ESPN(FootballWebsiteScraping):

    def __init__(self, url='http://games.espn.com/ffl/tools/projections?'):
        self.url = url

    def getWebsite(self, year, week, position=None, league=None):
        params = dict(scoringPeriodId = week,
                    seasonId = year,
                      )
        resp = requests.get(self.url, params=params)
        return resp

    def getNext(self, soup, original=True):
        link = soup.select("a[href*=startIndex]")  # href contains 'startIndex'
        #Check if this is page 0 not
        if not original and len(link) < 4:
            return []
        else:
            links = {"Link" : "",
                     "startIndex" : 0}
            for l in link:
                startIndex = int(l['href'].split("=")[-1])
                if startIndex > links['startIndex']:
                    links['Link'] = l['href']
                    links['startIndex'] = startIndex
            return links['Link']

    def getPlayerAttributes(self, attr):

        attr = str(attr).replace("*", "")
        if 'D/ST' in attr:
            l = attr.split(" ")
            name = l[0]
            team = l[0].upper()
            position = "DST"
        # Get normal players
        else:
            try:
                l = attr.split(",")
                name = l[0]
                team, position, *_ = l[1].upper().split("\xa0")
                #print(attr, "Name:%s, Team:%s, Position:%s" % (name.strip(), team.strip(), position.strip()))
            except:
                print("!!!!!Error", attr)
                raise
                quit()
        return name.strip(), team.strip(), position.strip()

    def writeResults(self, output_file):
        with open(output_file, 'w', newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow(['Player', 'Position', 'Team', 'Opponent', 'ESPN_FantasyPoints'])
            year, current_week = self.getWeek()
            resp = self.getWebsite(year, current_week)
            soup = BeautifulSoup(resp.text, 'html.parser')
            next = self.getNext(soup, original=True)
            while next:
                #table = soup.findAll('table')
                player_table = soup.find(lambda tag: tag.name == 'table' and tag.has_attr('id') and tag['id'] == 'playertable_0')

                rows = player_table.findAll('tr')

                data = []

                for row in rows:
                    cols = row.findAll('td')
                    cols = [ele.text.strip() for ele in cols]
                    data.append([ele for ele in cols if ele])  # get rid of empty values
                for d in data[2:]:
                    name, team, pos = self.getPlayerAttributes(d[0])
                    opponent = d[1].replace('@', "")
                    fantasy_prediction = d[-1:][0]
                    try:
                        writer.writerow([name, pos, team, opponent, fantasy_prediction])
                    except:
                        print(d)

                    #Get Next Page
                resp = requests.get(next)
                soup = BeautifulSoup(resp.text, 'html.parser')
                next = self.getNext(soup, original=False)
                #print(next)

class ffToday(FootballWebsiteScraping):

    def __init__(self, url='http://www.fftoday.com/rankings/playerwkproj.php?'):
        self.url = url

    def getPosition(self, position):
        posid = {"QB"   : "10",
                 "RB"   : "20",
                 "WR"   : "30",
                 "TE"   : "40",
                 "K"    : "80"}
        return posid[position]

    def getLeague(self, league):
        league = {"Default" : "1",
                  "PPR"     : "107644",
                  "Yahoo"   : "17",
                  "NFL.com" : "143908"}
        return league


    def writeResults(self, output_file):
        with open(output_file, 'w', newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow(['Player', 'Position', 'Team', 'Opponent', 'FantasyFootball_FantasyPoints'])
            year, current_week = self.getWeek()
            for position in ["QB", "WR", "TE", "RB", "K"]:
                resp = self.getWebsite(year, current_week, position, leagueID = "PPR")
                soup = BeautifulSoup(resp.text, 'html.parser')
                table = soup.findAll('table')

                try:
                    player_table = table[9]
                except:
                    print(self.getWeek(), position)
                    break

                rows = player_table.findAll('tr')

                data = []
                for row in rows:
                    cols = row.findAll('td')
                    cols = [ele.text.strip() for ele in cols]
                    data.append([ele for ele in cols if ele])  # get rid of empty values
                for d in data[3:]:
                    try:
                        writer.writerow([d[0], position, d[1], d[2], d[-1:][0]])
                    except:
                        print(d)

class fantasyData(FootballWebsiteScraping):

    def __init__(self, url="https://fantasydata.com/nfl-stats/fantasy-football-weekly-projections.aspx?"):
        self.url = url


    def getPosition(self, position):
        posid = {"QB"   : "2",
                 "RB"   : "3",
                 "WR"   : "4",
                 "TE"   : "5",
                 "K"    : "10",
                 "DST"  : "11"}
        return posid[position]

    def getSeason(self, year):
        current_year, _ = self.getWeek()
        season = current_year - year
        return season

    def getLeague(self, league):
        leagueID = {"Standard"    : "0",
                  "PPR"         : "1",
                  "FanDuel"     : "2",
                  "DraftKings"  : "3",
                  "Yahoo"       : "4",
                  "Half Pt PPR" : "5"}
        return leagueID[league]

    def getWebsite(self, year, week, position, league):
        params = dict(ls = '',
                      st = 'FantasyPointsDraftKings',
                      p = self.getPosition(position),  # Position, 1=QB, 2=RB, 3=WR, 4=TE, 5=K
                      sn = self.getSeason(year),  # Season, 4=2013, 3=2014, 2=2015, 1=2016, 0=2017
                      w = week - 1,  # week, week1 = 0, week2 = 1
                      ew = week - 1,  # end week
                      fs = self.getLeague(league),  # Scoring type, 0=standard, 1=PPR
                      stype = '0',
                      scope = '1',
                      s = "",
                      t = "0",
                      d = "1",
                      live = "False",
                      pid = "False",  # include playerID, these aren't the same playerids though
                      minsnaps = "4",
                      )
        resp = requests.get(self.url, params=params)
        return resp


    def writeResults(self, output_file):
        with open(output_file, 'w', newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow(['Player', 'Position', 'Team', 'Opponent', 'FantasyData_FantasyPoints'])
            year, current_week = self.getWeek()
            for position in ["QB", "WR", "TE", "RB", "K"]:
                resp = self.getWebsite(year, current_week, position, league="DraftKings")
                soup = BeautifulSoup(resp.text, 'html.parser')

                table = soup.findAll('table')

                # this table has all the player information in it, found through trial and error
                try:
                    player_table = table[0]
                except:
                    print(year, current_week, position)
                    break

                rows = player_table.findAll('tr')

                data = []
                for row in rows:
                    cols = row.findAll('td')
                    cols = [ele.text.strip() for ele in cols]
                    data.append([ele for ele in cols if ele])  # get rid of empty values
                for d in data[3:]:
                    # print(d)
                    name = d[1]
                    pos = d[2]
                    week = d[3]
                    team = d[4]
                    opponent = d[5]
                    fantasy_prediction = d[-1:][0]
                    try:
                        writer.writerow([name, pos, team, opponent, fantasy_prediction])
                    except:
                        print(d)

class fantasyStats(fantasyData):

    def __init__(self, url="https://fantasydata.com/nfl-stats/nfl-fantasy-football-stats.aspx?", league="DraftKings"):
        self.url = url
        self.league = league

    def grabPastResults(self, output_folder):
        current_year, current_week = self.getWeek()

        for year in range(2009, current_year):
            for week in range(1,17 + 1):
                print(year, "----", week)

                directory = "%s/%s/%s/" % (output_folder, year, week)
                if not os.path.exists(directory):
                    os.makedirs(directory)

                self.writeResults(output_folder,year, week)

        for week in range(1, current_week):
            print(current_year, "----", week)

            directory = "%s/%s/%s/" % (output_folder, current_year, week)
            if not os.path.exists(directory):
                os.makedirs(directory)

            self.writeResults(output_folder, current_year, week)

    def positionRows(self, position):
        if position == "QB":
            rows = ['Rank', 'Player', 'Position', 'Week', 'Team', 'Opponent',
                    'Comp', 'PassAtt', 'CompPct', 'PassYds', 'PassYdsPerAtt',
                    'PassTD', 'Interceptions', 'QBRating', 'RushAtt',
                    'RushYds', 'RushYdsPerAtt', 'RushTD', 'Points', 'Year']
        elif position == 'RB':
            rows = ['Rank', 'Player', 'Position', 'Week', 'Team', 'Opponent',
                    'RushAtt', 'RushYds', 'RushYdsPerAtt', 'RushTD', 'Targets',
                    'Rec', 'RecYds', 'RecTDs', 'Fumbles','FumLost', 'Points', 'Year']
        elif position == "WR":
            rows = ['Rank', 'Player', 'Position', 'Week', 'Team', 'Opponent',
                    'Targets', 'Rec', 'RecPct' 'RecYds', 'RecTDs', 'Long',
                    'YdsTarget', 'YdsPerRec', 'RushAtt', 'RushYds', 'RushTD',
                    'Fumbles', 'FumLost', 'Points', 'Year']
        elif position == "TE":
            rows = ['Rank', 'Player', 'Position', 'Week', 'Team', 'Opponent',
                    'Targets', 'Rec', 'RecPct' 'RecYds', 'RecTDs', 'Long',
                    'YdsTarget', 'YdsPerRec', 'RushAtt', 'RushYds', 'RushTD',
                    'Fumbles', 'FumLost', 'Points', 'Year']
        elif position == "K":
            rows = ['Rank', 'Player', 'Position', 'Week', 'Team', 'Opponent',
                    'FGMade', 'FGAtt', 'FGPct', 'FGLong', 'XPMade', 'XPAtt',
                    'Points', 'Year']
        elif position == "DST":
            rows = ['Rank', 'Player', 'Position', 'Week', 'Team', 'Opponent',
                    'TFL', 'Sacks', 'QBHits', 'Interceptions', 'FumRec',
                    'Safeties', 'DefTD', 'ReturnTD', 'PtsAllowed', 'Points',
                    'Year']
        return rows

    def writeResults(self, output_folder, year, week):

        for position in ["QB", "WR", "TE", "RB", "DST"]:
            filename = "%s/%d/%d/%s_data_%s.csv" % (output_folder, year, week, position, self.league)
            with open(filename, 'w', newline="") as csvfile:
                writer = csv.writer(csvfile, delimiter=",")
                writer.writerow(self.positionRows(position))
                week = int(week)
                year = int(year)
                resp = self.getWebsite(year, week, position, league=self.league)
                soup = BeautifulSoup(resp.text, 'html.parser')

                table = soup.findAll('table')

                # this table has all the player information in it, found through trial and error
                try:
                    player_table = table[0]
                except:
                    print(year, week, position)
                    break

                rows = player_table.findAll('tr')

                data = []
                for row in rows:
                    cols = row.findAll('td')
                    cols = [ele.text.strip() for ele in cols]
                    data.append([ele for ele in cols if ele])  # get rid of empty values
                for d in data[1:]:
                    d.append(year)
                    try:
                        writer.writerow(d)
                    except:
                        print(d)



class fantasyHistoryRotoGuru(fantasyData):
    #RotoGuru has historical data for player salaries and estimates.

    def __init__(self, url="http://rotoguru1.com/cgi-bin/fyday.pl?", league="DraftKings"):
        self.url = url
        self.league = league

    def grabPastResults(self, output_folder):
        current_year, current_week = self.getWeek()

        for year in range(2014, current_year):
            for week in range(1,17 + 1):
                print(year, "----", week)

                directory = "%s/%s/%s/" % (output_folder, year, week)
                if not os.path.exists(directory):
                    os.makedirs(directory)

                self.writeResults(output_folder,year, week)

        for week in range(1, current_week):
            print(current_year, "----", week)

            directory = "%s/%s/%s/" % (output_folder, current_year, week)
            if not os.path.exists(directory):
                os.makedirs(directory)

            self.writeResults(output_folder, current_year, week)


    def getWebsite(self, year, week, position, leagueID):
        params = dict(year = year,
                      week = week,
                      game = leagueID,
                      scsv = 1)
        resp = requests.get(self.url, params=params)
        return resp

    def writeResults(self, output_folder, year, week):


        filename = "%s/%d/%d/data_%s.csv" % (output_folder, year, week, self.league)
        with open(filename, 'w', newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow(["Week", "Year", "GID", "Name", "POS", "Team",
                             "Home/Away", "Oppt", "DraftKing Points", "Salary"
                             ])
            week = int(week)
            year = int(year)
            resp = self.getWebsite(year, week, None, leagueID="dk")
            soup = BeautifulSoup(resp.text, 'html.parser')

            table = soup.findAll('pre')

            # this table has all the player information in it, found through trial and error
            try:
                player_table = table[0]
            except:
                print(year, week)

            rows = player_table.text.splitlines()

            data = []
            for row in rows:
                cols = row.split(";")
                cols = [ele.strip() for ele in cols]
                data.append([ele for ele in cols if ele])  # get rid of empty values
            for d in data[1:]:
                try:
                    writer.writerow(d)
                except:
                    print(d)

if __name__ == "__main__":
    rg = fantasyHistoryRotoGuru()
    rg.grabPastResults(output_folder="weeklyCosts")
    #fs = fantasyStats()
    #fs.grabPastResults(output_folder="actualResults")


    '''
    #Setup
    ffToday = ffToday()
    fantasyData = fantasyData()
    ESPN = ESPN()
    CBS = CBS()
    year, current_week = ffToday.getWeek()
    
    directory = "weeklyProjections/%s/%s/" % (year, current_week)
    if not os.path.exists(directory):
        os.makedirs(directory)

    #Grab the CBS fantasy football data
    CBS.writeResults(directory + 'CBS_results.csv')

    #Grab the ESPN fantasy football data
    ESPN.writeResults(directory + 'ESPN_results.csv')

    # Grab football fantasy today data
    ffToday.writeResults("weeklyProjections/%s/%s/fftoday_results.csv" % (year, current_week))

    #Grab Fantasy Data
    fantasyData.writeResults("weeklyProjections/%s/%s/fantasyData_results.csv" % (year, current_week))
    '''