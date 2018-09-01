import pandas as pd
import os
import numpy as np
from scipy.optimize import minimize
from scipy.optimize import minpack as minpack2

import nflgame as nfl

import glob

class OptimizeDraft():

    def __init__(self, data, team={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "FLEX": 1, "DST": 1}, salary=50000):
        self.salary = salary
        self.team = team
        self.data = data
        self.type = 'Avg'

    def getType(self):
        return self.type

    def setType(self, type):
        types = ['Avg', 'Max', 'Min']
        if type not in types:
            quit("NO SET TYPE")
        self.type = type

    def pointOptimization(self, onTeam):
        #return -1 * sum(self.data['AvgPointsPerGame'] * onTeam)
        return -1 * sum(self.data[self.getType()] * onTeam)

    def constraintTeamCost(self, onTeam):
        #print(self.data.loc[self.data['onTeam'] == onTeam]['Salary'].sum())
        #return self.salary - sum(self.data['Salary'] * onTeam.round())
        #self.data['onTeam'] = onTeam
        #roundTeam = onTeam.copy().round()
        values = onTeam * self.data['Salary']
        #values2 = onTeam.round() * self.data['Salary']
        #print(values.sum(), values2.sum())
        #print(values.sum())
        #if (self.salary - self.data.loc[self.data['onTeam'] == onTeam]['Salary'].sum()) == 50000:
        #    self.data['onTeam'] = onTeam
        #    print(self.data.ix[self.data.onTeam > 0.5])
        return (self.salary - values.sum())

    def constraintPositionQB(self, onTeam):
        return self.team["QB"] - sum(self.data['QB'] * onTeam)

    def constraintPositionWR(self, onTeam):
        return (self.team["WR"] + self.FlexWR(onTeam)) - sum(self.data['WR'] * onTeam)

    def constraintPositionRB(self, onTeam):
        return (self.team["RB"] + self.FlexRB(onTeam)) - sum(self.data['RB'] * onTeam)

    def constraintPositionTE(self, onTeam):
        return (self.team["TE"] + self.FlexTE(onTeam)) - sum(self.data['TE'] * onTeam)

    def constraintPositionDST(self, onTeam):
        return self.team["DST"] - sum(self.data['DST'] * onTeam)

    def FlexWR(self, onTeam):
        return 0

    def FlexRB(self, onTeam):
        return 1

    def FlexTE(self, onTeam):
        return 0

    def constraintPositionFlex(self, onTeam):
        res = self.team['FLEX'] - (self.FlexRB(onTeam) + self.FlexTE(onTeam) + self.FlexWR(onTeam))
        return res

    def constraintBinary(self, onTeam):
        return sum(onTeam) - sum(onTeam.round())

    def optimizeLineup(self):
        #https://orbythebeach.wordpress.com/2015/09/28/how-to-build-the-best-fantasy-football-team/
        constraights = (
            {"type": "ineq", "fun": self.constraintTeamCost},
            {"type" : "eq" , "fun":self.constraintPositionDST},
            {"type": "eq", "fun": self.constraintPositionQB},
            {"type": "eq", "fun": self.constraintPositionRB},
            {"type": "eq", "fun": self.constraintPositionWR},
            {"type": "eq", "fun": self.constraintPositionTE},)

        b = (0, 1)
        bnds = tuple()
        for p in self.data['onTeam']:
            bnds = (b,) + bnds
        res = minimize(self.pointOptimization, self.data['onTeam'].copy(), method='SLSQP', bounds=bnds, constraints=constraights)
        print(res.fun)
        return res

    def optimize(self, type='Avg'):
        self.setType(type)
        res = self.optimizeLineup()
        players['onTeam'] = res.x.round()
        team = players[players.onTeam == 1]
        bestTeam = players[players.onTeam == 1]
        directory = "teams/%s/%s/" % (year, current_week)
        if not os.path.exists(directory):
            os.makedirs(directory)
        bestTeam.to_csv(directory + "%s_%s_BestTeam.csv" % (res.fun, type))
        print(team.Salary.sum())
        quit()

if __name__ == "__main__":


    # https://orbythebeach.wordpress.com/2015/09/28/how-to-build-the-best-fantasy-football-team/
    year, current_week = nfl.live.current_year_and_week()
    year, current_week = 2017, 16

    path = "weeklyData/%s/%s/data.csv" % (year, current_week)
    players = pd.read_csv(path)
    #print(players.head(10))
    players['onTeam'] = 1
    players['QB'] = 0
    players['RB'] = 0
    players['WR'] = 0
    players['TE'] = 0
    players['DST'] = 0
    team = {"QB": 1, "RB": 2, "WR": 3, "TE": 1, "FLEX": 1, "DST": 1}
    #print(players.head(10))
    for index, row in players.iterrows():
        if row.Position == "QB":
            players.set_value(index, 'QB', 1)
        elif row.Position == "RB":
            players.set_value(index, 'RB', 1)
        elif row.Position == "WR":
            players.set_value(index, 'WR', 1)
        elif row.Position == "TE":
            players.set_value(index, 'TE', 1)
        elif row.Position == "DST":
            players.set_value(index, 'DST', 1)
        #df = players[['onTeam', 'QB', 'RB', 'WR', 'TE', 'DST', 'Salary', 'AvgPointsPerGame']]
    #for index, row in players.iterrows():
    #    if row.Position is not "DST" and row.isnull().values.any():
    #        if row.FantasyPoints_x ==
    dst = players.ix[players.Position == "DST"]
    players = players.dropna(subset=['ESPN_FantasyPoints', 'FantasyData_FantasyPoints', 'FantasyFootball_FantasyPoints'], thresh=2, axis='index', how='any')
    players = players.append(dst)

    df = players[['onTeam', 'QB', 'RB', 'WR', 'TE', 'DST', 'Salary', 'Avg', 'Max', 'Min']]
    #print(df)
        #print(players['DST'].sum())
    od = OptimizeDraft(df,
                       team={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "FLEX": 1, "DST": 1},
                       salary=50000)
    for type in ['Max', 'Avg', 'Min']:
        od.optimize(type=type)

        path = "teams/%s/%s/" % (year, current_week)
        extension = "*%s_BestTeam.csv" % type
        files = [i for i in glob.glob(path + '{}'.format(extension))]
        bestTeam = pd.read_csv(files[0])

    for index, row in bestTeam.iterrows():
        # df = players[['onTeam', 'QB', 'RB', 'WR', 'TE', 'DST', 'Salary', 'AvgPointsPerGame']].drop(index, axis=0).copy()
        df = players[['onTeam', 'QB', 'RB', 'WR', 'TE', 'DST', 'Salary', 'Avg']].drop(index, axis=0).copy()

        od = OptimizeDraft(df,
                           team={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "FLEX": 1, "DST": 1},
                           salary=50000)
        res = od.optimizeLineup()
        #df['onTeam'] = res.x.round()
        Team = df[df.onTeam > 0]
        filename = "%s-Best-%s.csv" % (res.fun, index)
        Team.to_csv(path + filename)
    '''
    res = od.optimizeLineup()
    players['onTeam'] = res.x.round()
    print(players[players.onTeam == 1])
    bestTeam = players[players.onTeam == 1]
    directory = "teams/%s/%s/" % (year, current_week)
    if not os.path.exists(directory):
        os.makedirs(directory)
    bestTeam.to_csv(directory + "bestTeam.csv")
    for index,row in bestTeam.iterrows():
        #df = players[['onTeam', 'QB', 'RB', 'WR', 'TE', 'DST', 'Salary', 'AvgPointsPerGame']].drop(index, axis=0).copy()
        df = players[['onTeam', 'QB', 'RB', 'WR', 'TE', 'DST', 'Salary', 'Avg']].drop(index, axis=0).copy()

        od = OptimizeDraft(df,
                           team={"QB": 1, "RB": 2, "WR": 3, "TE": 1, "FLEX": 1, "DST": 1},
                           salary=50000)
        res = od.optimizeLineup()
        df['onTeam'] = res.x.round()
        Team = df[df.onTeam == 1]
        filename = "Best-%s-%s.csv" % (index, res.fun)
        Team.to_csv(directory + filename)
        '''
    '''
class FarmerProblem():
    def __init__(self, df, land, fertilizer, labor):
        self.land = land
        self.fert = fertilizer
        self.labor = labor
        self.df = df

    def land_constraight(self, df):
        land = self.land - sum(df * self.df['Land'])
        print("Land", land)
        return land

    def labor_constraight(self, df):
        labor = self.labor - sum(df * self.df['Labor'])
        print("Labor", labor)
        return labor

    def fertilizer_constraight(self, df):
        fertilizer = self.fert - sum(df * self.df['Fertilizer'])
        print("Fertilizer", fertilizer)
        return fertilizer

    def profit(self, df):
        profit = -1 * sum(df * self.df['Profit'])
        print("Profit", df, profit)
        return profit

    def farmerProblem(self):
        cons = ({'type': 'eq', 'fun': self.land_constraight},
                {'type': 'ineq', 'fun': self.labor_constraight},
                {'type': 'ineq', 'fun': self.fertilizer_constraight})
        b = (0, 100)
        bnds = (b, b, b)
        sol = minimize(self.profit, self.df['Plant'].copy(), method='SLSQP', bounds=bnds, constraints=cons)
        print(sol)

if __name__ == "__main__":


    df = pd.DataFrame([[20, 3, 1, 2, 300],[15, 2, 1, 4, 600],[10, 1, 1, 1, 200]], columns=['Plant', 'Labor', 'Land', 'Fertilizer', 'Profit'])
    f = FarmerProblem(df, 45, 120, 120)
    f.farmerProblem()
'''