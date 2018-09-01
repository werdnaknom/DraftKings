import nflgame as nfl

import pandas as pd
import numpy as np

import glob
import os

from time import sleep


def createPredictionMatrix():
    year, current_week = nfl.live.current_year_and_week()
    # Grab prediction files and clean them
    pred = CombinePredictions()
    cost = CombineCosts()
    predictions = pred.grabFiles(year, current_week)
    for f in predictions:
        if "_cleaned" not in f:
            pred.createClean(f)
    # Grab cost files and clean them
    costs = cost.grabFiles(year, current_week)
    for f in costs:
        if "_cleaned" not in f:
            cost.createClean(f)

    # Grab all the clean files and extract them as DataFrames
    prediction_files = pred.grabFiles(year, current_week)
    cost_files = cost.grabFiles(year, current_week)
    prediction_frames = pred.extractFiles(prediction_files)
    cost_frames = cost.extractData(cost_files)

    # print(c_df[c_df[c_df.isnull().any()]])
    # print("---------------------------------")
    # Combine the prediction files and then combine the cost file
    p_df = pred.mergeFrames(prediction_frames)

    c_df = cost_frames[0]
    f_df = cost.mergeFrames([c_df, p_df], how='left')

    # Calculate the avg of the prediction data
    # print(f_df.columns)
    f_df["Avg"] = f_df[["ESPN_FantasyPoints", "FantasyData_FantasyPoints",
                        "FantasyFootball_FantasyPoints", "CBS_FantasyPoints",
                        "AvgPointsPerGame"]].mean(axis=1)
    f_df["Max"] = f_df[["ESPN_FantasyPoints", "FantasyData_FantasyPoints",
                        "FantasyFootball_FantasyPoints", "CBS_FantasyPoints",
                        "AvgPointsPerGame"]].max(axis=1)
    f_df["Min"] = f_df[["ESPN_FantasyPoints", "FantasyData_FantasyPoints",
                        "FantasyFootball_FantasyPoints", "CBS_FantasyPoints",
                        "AvgPointsPerGame"]].min(axis=1)
    # Write to file
    # print(f_df)
    # f_df = f_df.ix['Player', 'Position']
    f_df = f_df[[
        'Player', 'Position', 'Team', 'Salary', 'ESPN_FantasyPoints',
        'FantasyData_FantasyPoints', "FantasyFootball_FantasyPoints", "CBS_FantasyPoints",
        'AvgPointsPerGame', 'Avg', 'Max', 'Min']]

    pred.writeFile(f_df, year, current_week)

    # cleanFantasyData(df, year, current_week)


def createResultsMatrix(new_matrix=False):
    results = CombineResults()
    if new_matrix:
        extension = "csv"
        year_folders = [i for i in glob.glob("actualResults/*")]

        for yf in year_folders:
            year = yf.split('actualResults\\')[1]

            week_folders = [i for i in glob.glob(yf + "/*")]

            for wf in week_folders:
                week = wf.split(yf + '\\')[1]

                res = results.grabFiles(year, week)
                for f in res:
                    if "_cleaned" not in f:
                        results.createClean(f)


def removeNaN(df):
    '''
    #TODO: Need to figure out how to not drop Defense
    if df.isnull().values.any():
        print(df.isnull().values)
        df = df.dropna()
        print(df.isnull().values.any())
    return df
    '''
    return df

class Combine(object):

    def extractFiles(self, path):
        extension = "csv"
        files = [i for i in glob.glob(path + '*.{}'.format(extension))]
        return files

    def grabFiles(self, year, week, directory):
        # Find all files with extension at path
        path = "%s/%s/%s/" % (year, week, directory)
        files = self.extractFiles(path)
        return files

    def extractData(self, files):
        frames = []
        for f in files:
            if "_cleaned" in f:
                df = pd.read_csv(f, header=0)
                frames.append(df)
        return frames

    def createClean(self, filename):
        df = pd.read_csv(filename, header=0)
        df['PlayerID'] = ""
        clean_df = self.clean(df)

        new_file = filename.replace(".csv", "")
        new_file = new_file + "_cleaned.csv"
        clean_df.to_csv(new_file)

    def clean(self, df):
        for index, row in df.iterrows():
            if row.Team == "LAR":
                row.Team = "LA"
                df.set_value(index, col="Team", value="LA")
            elif row.Team == "JAC":
                row.Team = "JAX"
                df.set_value(index, col="Team", value="JAX")
            if row.Position != "DST":
                found, player = self.findPlayer(row)
                if found:
                    df.set_value(index, col="PlayerID", value=player.playerid)
                else:
                    # print(index)
                    # print(row.Player)
                    df.drop(df.index[int(index)])
        return df

    def findPlayer(self, row):
        first, last, *_ = row.Player.split(" ")
        name = first + " " + last
        found = nfl.find(name, row.Team)
        if row.Position == "DST":
            return False, "Defense"
        if len(found) == 1:
            player = found[0]
            return True, player
        elif len(found) == 0:
            found = nfl.find(name)
            if len(found) == 0:
                year, current_week = nfl.live.current_year_and_week()
                # print(row.Team, row)
                try:
                    for game in nfl.games(year, home=row.Team, away=row.Team):
                        #print(game, row.Team, year)
                        try:
                            player = game.players.name(first[0] + "." + last)
                            if player != None:
                                if player.team == row.Team:
                                    return True, player
                                    break

                        except:
                            # print(row.Player)
                            quit()
                except:
                    print(row)
                    print(name)
                    raise

            else:
                if len(found) > 1:
                    for player in found:
                        if player.position == row.Position:
                            return True, player
                else:
                    return True, found[0]
        else:
            return False, 0
        return False, 0

    def mergeFrames(self, frames, how='outer'):
        # for df in frames:
        #    df.set_index('Player', inplace=True)
        # df = pd.concat(frames, axis=0)
        try:
            for i, df in enumerate(frames):
                frames[i] = df.drop('Opponent', axis=1)
        except ValueError:
            pass
        df = frames[0]
        for frame in frames[1:]:
            #print(frame.columns)
            fantasyPoints = frame.columns[-2]  # second to last column is Fantasy Points
            frame = frame[['PlayerID', 'Position', 'Team', fantasyPoints]]
            df = pd.merge(left=df, right=frame, how=how, on=['PlayerID', 'Position', 'Team'])
        return df

    def averagePoints(self, df):
        df.set_index('Player', inplace=True)
        df = df.ix[:, 2:]
        df['Avg'] = df.mean(axis=1)
        # print(df)

    def writeFile(self, df, year, week):
        directory = "weeklyData/%s/%s/" % (year, week)
        if not os.path.exists(directory):
            os.makedirs(directory)
        df.to_csv(directory + "data.csv")


class CombineResults(Combine):

    def grabFiles(self, year, week, directory='actualResults'):
        # Find all files with extension at path
        path = "%s/%s/%s/" % (year, week, directory)
        files = self.extractFiles(path)
        return files

class CombinePredictions(Combine):

    def grabFiles(self, year, week, directory='weeklyProjections'):
        # Find all files with extension at path
        path = "%s/%s/%s/" % (year, week, directory)
        files = self.extractFiles(path)
        return files

class CombineCosts(Combine):

    def grabFiles(self, year, week, directory='weeklyCosts'):
        # Find all files with extension at path
        path = "%s/%s/%s/" % (year, week, directory)
        files = self.extractFiles(path)
        return files

    def mergeFrames(self, frames, how='outer'):
        # for df in frames:
        #    df.set_index('Player', inplace=True)
        # df = pd.concat(frames, axis=0)
        try:
            for i, df in enumerate(frames):
                frames[i] = df.drop('Opponent', axis=1)
        except ValueError:
            pass
        cost_df = frames[0]
        for frame in frames[1:]:
            # fantasyPoints = frame.columns[-3:] #second to last column is Fantasy Points
            frame = frame[['PlayerID', 'Position', 'Team', 'ESPN_FantasyPoints',
                           'FantasyData_FantasyPoints', 'FantasyFootball_FantasyPoints', 'CBS_FantasyPoints']]
            # quit()
            df = pd.merge(left=cost_df, right=frame, how=how, on=['PlayerID', 'Position', 'Team'])
        return df

    def createClean(self, filename):
        df = pd.read_csv(filename, header=0)
        df['PlayerID'] = ""
        df = df.rename(index=str, columns={"Name": "Player", "teamAbbrev": "Team", "GameInfo": "Opponent"})
        clean_df = self.clean(df)

        new_file = filename.replace(".csv", "")
        new_file = new_file + "_cleaned.csv"
        clean_df.to_csv(new_file)

class historicalCombine(Combine):

    def combineHistorical(self):

        path = r'weeklyCosts\*\*\\'
        extension = "data_DraftKings.csv"
        # files = glob.glob(path + extension)
        files = glob.glob(path + "*")

        # files = glob.glob("weeklyCosts/*/15/" + extension)
        # print(path)
        # print(extension)
        print(files)
        quit()

        list_ = [pd.read_csv(file, index_col=None, header=0) for file in files]
        frame = pd.concat(list_, ignore_index=True)
        return frame


    def cleanHistorical(self, frame):
        frame['Team'] = frame['Team'].replace('nor', 'NO')
        frame['Team'] = frame['Team'].replace('sfo', 'SF')
        frame['Team'] = frame['Team'].replace('tam', 'TB')
        frame['Team'] = frame['Team'].replace('sdg', 'SD')
        frame['Team'] = frame['Team'].replace('kan', 'KC')
        frame['Team'] = frame['Team'].replace('nwe', 'NE')
        frame['Team'] = frame['Team'].replace('gnb', 'GB')
        frame['Team'] = frame['Team'].replace('lar', 'LA')
        frame['Team'] = frame['Team'].replace('lac', 'SD')

        frame['Oppt'] = frame['Oppt'].replace('nor', 'NO')
        frame['Oppt'] = frame['Oppt'].replace('sfo', 'SF')
        frame['Oppt'] = frame['Oppt'].replace('tam', 'TB')
        frame['Oppt'] = frame['Oppt'].replace('sdg', 'SD')
        frame['Oppt'] = frame['Oppt'].replace('kan', 'KC')
        frame['Oppt'] = frame['Oppt'].replace('nwe', 'NE')
        frame['Oppt'] = frame['Oppt'].replace('gnb', 'GB')
        frame['Oppt'] = frame['Oppt'].replace('lar', 'LA')
        frame['Oppt'] = frame['Oppt'].replace('lac', 'SD')

        frame['POS'] = frame['POS'].replace('Def', 'DST')

        frame['Team'] = frame['Team'].str.upper()
        frame['Oppt'] = frame['Oppt'].str.upper()

        frame.to_csv("weeklyCosts/combinedWeeklyCost.csv")

    def createClean(self, filename):
        df = pd.read_csv(filename, header=0)
        df['PlayerID'] = ""
        df = df.rename(index=str, columns={"Oppt": "Opponent", "POS" : "Position", "Name" : "Player"})
        clean_df = self.clean(df)

        new_file = filename.replace(".csv", "")
        new_file = new_file + "_cleaned.csv"
        clean_df.to_csv(new_file)

    def findPlayer(self, row):
        last, first, *_ = row.Player.split(" ")
        name = first + " " + last
        name = name.replace(",", "")
        name = name.replace(".", "")
        found = nfl.find(name, row.Team)
        if row.Position == "DST":
            return False, "Defense"
        if len(found) == 1:
            player = found[0]
            return True, player
        elif len(found) == 0:
            found = nfl.find(name)
            if len(found) == 0:
                year, current_week = nfl.live.current_year_and_week()
                # print(row.Team, row)
                try:
                    for game in nfl.games(year, home=row.Team, away=row.Team):
                        #print(game, row.Team, year)
                        try:
                            player = game.players.name(first[0] + "." + last)
                            if player != None:
                                if player.team == row.Team:
                                    return True, player
                                    break

                        except:
                            # print(row.Player)
                            quit()
                except:
                    print(row)
                    print(name)
                    raise

            else:
                if len(found) > 1:
                    for player in found:
                        if player.position == row.Position:
                            return True, player
                else:
                    return True, found[0]
        else:
            return False, 0
        return False, 0


if __name__ == "__main__":

    #createResultsMatrix(new_matrix=True)
    hist = historicalCombine()
    frame = hist.combineHistorical()
    hist.cleanHistorical(frame)
    hist.createClean("weeklyCosts/combinedWeeklyCost.csv")
    #createPredictionMatrix()

    '''
    def createPredictionMatrix():

        year, current_week = nfl.live.current_year_and_week()
        # Grab prediction files and clean them
        predictions = self.grabPredictionFiles(year, current_week)
        for f in predictions:
            if "_cleaned" not in f:
                cleanPredictions(f)
        # Grab cost files and clean them
        costs = grabCostFiles(year, current_week)
        for f in costs:
            if "_cleaned" not in f:
                cleanCosts(f)

        # Grab all the clean files and extract them as DataFrames
        prediction_files = grabPredictionFiles(year, current_week)
        cost_files = grabCostFiles(year, current_week)
        prediction_frames = extractData(prediction_files)
        cost_frames = extractData(cost_files)

        # print(c_df[c_df[c_df.isnull().any()]])
        # print("---------------------------------")
        # Combine the prediction files and then combine the cost file
        p_df = combineFrames(prediction_frames)

        c_df = cost_frames[0]
        f_df = combineCostFrames([c_df, p_df], how='left')

        # Calculate the avg of the prediction data
        print(f_df.columns)
        f_df["Avg"] = f_df[["ESPN_FantasyPoints", "FantasyData_FantasyPoints",
                            "FantasyFootball_FantasyPoints", "CBS_FantasyPoints",
                            "AvgPointsPerGame"]].mean(axis=1)
        f_df["Max"] = f_df[["ESPN_FantasyPoints", "FantasyData_FantasyPoints",
                            "FantasyFootball_FantasyPoints", "CBS_FantasyPoints",
                            "AvgPointsPerGame"]].max(axis=1)
        f_df["Min"] = f_df[["ESPN_FantasyPoints", "FantasyData_FantasyPoints",
                            "FantasyFootball_FantasyPoints", "CBS_FantasyPoints",
                            "AvgPointsPerGame"]].min(axis=1)
        # Write to file
        # print(f_df)
        # f_df = f_df.ix['Player', 'Position']
        f_df = f_df[[
            'Player', 'Position', 'Team', 'Salary', 'ESPN_FantasyPoints',
            'FantasyData_FantasyPoints', "FantasyFootball_FantasyPoints", "CBS_FantasyPoints",
            'AvgPointsPerGame', 'Avg', 'Max', 'Min']]

        writeFile(f_df, year, current_week)

        # cleanFantasyData(df, year, current_week)
    '''

    '''
    year, current_week = nfl.live.current_year_and_week()
    #Grab prediction files and clean them
    predictions = grabPredictionFiles(year, current_week)
    for f in predictions:
        if "_cleaned" not in f:
            cleanPredictions(f)
    #Grab cost files and clean them
    costs = grabCostFiles(year, current_week)
    for f in costs:
        if "_cleaned" not in f:
            cleanCosts(f)

    #Grab all the clean files and extract them as DataFrames
    prediction_files = grabPredictionFiles(year, current_week)
    cost_files = grabCostFiles(year, current_week)
    prediction_frames = extractData(prediction_files)
    cost_frames = extractData(cost_files)
    '''

    '''
    DON'T READD THIS
    for df in prediction_frames:
        df = removeNaN(df)
    for df in cost_frames:
        df = removeNaN(df)
    '''

    '''
    #print(c_df[c_df[c_df.isnull().any()]])
    #print("---------------------------------")
    #Combine the prediction files and then combine the cost file
    p_df = combineFrames(prediction_frames)

    c_df = cost_frames[0]
    f_df = combineCostFrames([c_df, p_df], how='left')

    #Calculate the avg of the prediction data
    print(f_df.columns)
    f_df["Avg"] = f_df[["ESPN_FantasyPoints", "FantasyData_FantasyPoints",
                        "FantasyFootball_FantasyPoints", "CBS_FantasyPoints",
                       "AvgPointsPerGame"]].mean(axis=1)
    f_df["Max"] = f_df[["ESPN_FantasyPoints", "FantasyData_FantasyPoints",
                        "FantasyFootball_FantasyPoints", "CBS_FantasyPoints",
                        "AvgPointsPerGame"]].max(axis=1)
    f_df["Min"] = f_df[["ESPN_FantasyPoints", "FantasyData_FantasyPoints",
                        "FantasyFootball_FantasyPoints", "CBS_FantasyPoints",
                        "AvgPointsPerGame"]].min(axis=1)
    #Write to file
    #print(f_df)
    #f_df = f_df.ix['Player', 'Position']
    f_df = f_df[[
        'Player', 'Position', 'Team', 'Salary', 'ESPN_FantasyPoints',
        'FantasyData_FantasyPoints',"FantasyFootball_FantasyPoints", "CBS_FantasyPoints",
        'AvgPointsPerGame', 'Avg', 'Max', 'Min']]

    writeFile(f_df, year, current_week)

    #cleanFantasyData(df, year, current_week)
    '''

    '''
    DONT READD THIS
    cost_files = grabCostFiles(year, current_week)
    prediction_frames = extractData(prediction_files)
    cost_frames = extractData(cost_files)
    c_df = cost_frames[0].rename(index=str, columns={"Name" : "Player", "teamAbbrev" : "Team", "GameInfo" : "Opponent"})
    p_df = combineFrames(prediction_frames)
    f_df = combineFrames([p_df, c_df], how='right')
    f_df["Avg"] = f_df[["FantasyPoints_x", "FantasyPoints_y", "AvgPointsPerGame"]].mean(axis=1)
    writeFile(f_df, year, current_week)
    '''