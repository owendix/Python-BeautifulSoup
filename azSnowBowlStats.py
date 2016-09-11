# -*- coding: utf-8 -*-
"""
Search through: http://arizonasnowbowl.com/ for snow and weather stats

Get snow depth range, base and peak snow in past 24 hours, 
the current high, snow conditions, road conditions, and weather conditions

Output:
csv file: azSnowBowlStats.csv

Uses BeautifulSoup and urllib
Uses nested dict comprehensions
"""
from bs4 import BeautifulSoup
import re, os.path, sys, requests
from datetime import date
from pandas import Series, DataFrame
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def getNumbers(aString):

    """Retrieve a list of numbers within a string
    
    Arguments:
    aString -- a string containing some numbers
    Returns:
    theNumbers -- a list of numbers separated in input by other text
    
    #doctest example:
    >>> getNumbers('ab12c3d45ef')
    [12, 3, 45]
    
    #Notes:
    #copy and paste results into docstring, stored in __doc__
    #blank space must appear after input >>>
    #blank line must appear after end of results
    #to run doctest:
    #import doctest
    #import azSnowBowlStats
    #doctest.testmod(m='azSnowBowlStats')
    #or
    #doctest.testmod(m='azSnowBowlStats',verbose=True)
    """
    theNumbers = []
    for x in re.findall('\d+',aString):
        if x.isnumeric():
            theNumbers.append(int(x))
    
    return theNumbers

def lStripWeekday(string):
    
    """Remove Weekday and trailing space and dash from beginning of string
    
    Argument:
    string -- a string, with a possible weekday name at the beginning
    
    Return:
    string with weekday and following dash and space
    
    doctest:
    >>> lStripWeekday('Happy Tuesday - The temperature is 57 on this Tuesday')
    'The temperature is 57 on this Tuesday'
    
    
    """
    
    iMax = 20
    for chars in ['Monday','Tuesday','Wednesday',
        'Thursday','Friday','Saturday','Sunday']:
        
        i = string.find(chars,0,iMax)
        if i != -1 and not string[i+1].isnumeric():
            #strip off the day of the week (boring)
            string = string[i+len(chars)+1:]
            string = string.lstrip(' ,-')

    return string
        


def roadHazard(rdCondStr):
    
    """"Return road hazard level (0-4) for a given road condition string
    
    Argument:
    rdCondStr: a string describing the road conditions
    
    Return:
    Integer value where 0 is no hazard and 4 is high hazard
    
    doctest:
    >>> roadHazard('Clear')
    0
    
    >>> roadHazard('Plowed and cindered')
    1
    
    >>> roadHazard('Icy in some spots')
    2
    
    >>> roadHazard('4WD or chains recommended')
    3
    
    >>> roadHazard('4WD or chains required')
    4
    
    """

    r = rdCondStr.lower()

    w34 = ['chains','4x4','4wd']
    w4 = ['requir','need','mandat','must','neces']
    w3 = ['recom','sugg','shou','may','might','coul','desir','want']
    
    for w in w34:
        if w in r:
            for x in w4:                
                if x in r and 'no' not in r:
                    return 4
                else:
                    for y in w3:
                        if y in r:
                            return 3
    
    #reached here: hazard level = 0, 1, or 2
    w2 = ['icy','ice','slick','slip']
    w1 = ['plow','cind']
    
    for w in w2:
        if w in r:
            return 2
    for x in w1:
        if x in r:
            return 1
        
    #no hazard words detected
    return 0
    
def snowHazard(snwCondStr):
    
    """Return the snow hazard level (0-5) for a given snow condition string
    
    Argument:
    snwCondStr: a string describing the snow conditions
    
    Return:
    An integer from 0-5 where 0 is no hazard and 5 is high hazard
    
    doctest:
    >>> snowHazard('Fresh powder and groomed variable conditions')
    2
    
    >>> snowHazard('Groomed variable conditions')
    4
    
    >>> snowHazard('Packed powder and groomed variable conditions')
    3  

    >>> snowHazard('Packed powder')
    2
    
    >>> snowHazard('Powder and Packed Powder conditions')
    1
    
    >>> snowHazard('Spring like conditions')
    5
    
    >>> snowHazard('Trace of New - Powder and packed powder')
    1
    
    >>> snowHazard('Fresh powder')
    0
    
    
    """
    
    
    s = snwCondStr.lower()
    
    w4=['spring','summ','ice','hard','icy']
    w3='groom'
    w1='pack'
    wavg = 'and'
    
    for w in w4:
        if w in s:
            return 5

    h = np.array([])        
    
    if w3 in s:
        h = np.append(h,4)
    if w1 in s:
        h = np.append(h,2)
    if wavg in s:
        if len(h) < 2:
            h = np.append(h,0)
    elif len(h) == 0:
        h = np.append(h,0)
    
    return int(h.mean())

    

def getConditions():


    keys = ['Base Depth','24 hours','Surface','Road','Current']
    stats = {key:None for key in keys}
    
        
    try:
        site = 'http://arizonasnowbowl.com/'
        resp = requests.get(site)
        soup = BeautifulSoup(resp.content)
        assert soup is not None
    except AssertionError:
        print('No data retrieved from http://arizonasnowbowl.com/')
        sys.exit()

    try:
        tds = soup.find_all('td')
        #asserts tds is not empty (false if empty)
        assert tds
    except AssertionError:
        print('No td tags: error retrieved from http://arizonasnowbowl.com/')
        sys.exit()
    
    #nested dict comprehension
    stats = {key:str.strip(tds[i+1].getText())
        for i,tag in enumerate(tds) for key in keys
        if key in tag.getText()
        }
    
    #Strip off opening weekday

    stats['Current'] = lStripWeekday(stats['Current'])
    
    #rekey stats dictionary, want reverse order for first loop
    oldKeys = keys[1::-1]
    newKeys = [('NewBaseSnow', 'NewPeakSnow'),
               ('MinDepth','MaxDepth')
               ]
    for i,ok in enumerate(oldKeys):
        (nk1,nk2) = newKeys[i]
        depthRg = getNumbers(stats[ok])
        #Works even if range includes just 1 number
        stats[nk1], stats[nk2] = depthRg[0], depthRg[-1]

        keys.remove(ok)
        #I know its slow but its short and sweet
        keys.insert(0,nk2)
        keys.insert(0,nk1)
        stats.pop(ok)

    oldKeys = keys[4:]
    for i,ok in enumerate(oldKeys):
        if ok == 'Current':
            nk = 'WeatherCond'
        elif ok == 'Surface':
            nk = 'SnowCond'
        else:
            nk = ok + 'Cond'
        #Commas in strings mess with pandas.read_csv()
        stats[nk] = stats[ok].replace(',','')
        keys[i+4] = nk
        stats.pop(ok)
    
    #Add snow and road hazard levels
    stats['SnowHazard'] = snowHazard(stats['SnowCond'])
    stats['RoadHazard'] = roadHazard(stats['RoadCond'])
    keys.append('SnowHazard')
    keys.append('RoadHazard')
    
    #insert today's date
    keys.insert(0,'Date')
    stats[keys[0]] = date.today().isoformat()
    keys.insert(1,'Weekday')
    stats[keys[1]] = date.today().strftime("%A")
    keys.insert(6,'Temp')
    #date.today().isoformat()
    
    #re_weather = re.compile('wea[th][th]er*')
    #Note condition is spelled wrong in div's class_
    #re_condition = re.compile('.*cond*tion')
    re_degree = re.compile('.*degree')
    tag = soup.find(class_=re_degree)
    #High Temp
    #getNumbers returns a list
    [stats[keys[6]]] = getNumbers(str.strip(tag.find('h1').getText()))
    
    return [stats,keys]
     

def getLiftsTrails():


    try:
        site = 'http://arizonasnowbowl.com/?q=node/133'
        resp = requests.get(site)
        soup = BeautifulSoup(resp.content)
        assert soup is not None
    except AssertionError:
        print('No data retrieved from http://arizonasnowbowl.com/?q=node/133')
        sys.exit()
        
    snowRep = soup.find_all(class_='SnowReport')
        
    #lift information
    l = snowRep[1].get_text().strip().splitlines()
    l = [x.strip() for x in l[1:] if x != '']
    #Only real lifts, not conveyors
    lifts = dict()
    for i,s in enumerate(l):
        if i%2 == 0:
            k = s
        else:
            v = s
        if i > 0 and k.find('onveyor') == -1:
            lifts[k]=v
        
    #Trails open snowRep[2]
    ts = snowRep[2].find_all('td')
    trails=dict()
    for t in ts:
        ks=t.getText().strip().splitlines()
        if len(ks) > 0:
            k = ks[0]
            if 'deactive' in str(t.img):
                v='Closed'
            else:
                v='Open'
            trails[k]=v
    
    return [lifts, trails]    
    
def getNOpen(d):
    #d is a dict
    nOpen = len([x for x in d.values() if x != 'Closed'])
    n = len(d)
    if n > 0:    
        #return format(nOpen/n*100,'.1f')+'%'
        return [nOpen,n]
    else:
        return [None,None]


def getStats(filename):
    
    df = pd.read_csv(filename,index_col = 0,parse_dates=True)
    
    return df
    

def makeTrainingFile(df,yStr='SnowHazard',nDays=1,shift_ns=True,
                     header=False,index=False
                     ):
    
    """Make training data to predict the column yStr
    
        
    
    Concatenates the following for predictors of SnowHazard[0-4] or 
    RoadHazard[0-4] for the next day:
    
    Weekday[0-6], NewBaseSnow, Temp, SnowHazard[0-5], RoadHazard[0-4]
    
    If I want to make a prediction further in the future, 
    I can input data from the weather channel into predictBothHazards
    
    Arguments:
    
    df:     data frame of input data, from getStats
    
    yStr:   either 'SnowHazard' or 'RoadHazard'
    
    
    Return:
    yStrData.txt: SnowHazardData.txt or RoadHazardData.txt 
        concatenates input data from one day and concatenates
        with SnowHazard or RoadHazard data for the following day, for use
        with logisticRegression

    """
    columns = ['NewBaseSnow','Temp','SnowHazard','RoadHazard']

    #concatenate multiple days if nDays > 1
    nDays = int(nDays)
    dMax = 14
    if nDays > dMax:
        nDays = dMax
    elif nDays < 1:
        nDays = 1


    if shift_ns:
        #shift newbasesnow back one day (fits index better than shifting
        #others forward
        newDF = pd.concat([df[columns[0]].shift(-1),df[columns[1:]]],
                           axis=1
                           )
    else:
        newDF = df[columns]
        
    #interpolate   
    newDF = newDF.asfreq(freq='D').interpolate().round()
    newDF.loc[:,'Weekday'] = Series(newDF.index.dayofweek,index=newDF.index)
    #reorder columns    
    columns.insert(0,'Weekday')
    newDF = newDF[columns]

    #works for nDays = 1 - dMax
    dfs = [newDF.shift(nDays - i - 1) 
        for i in range(nDays)
        ]
    colKeys = [str(nDays-i)+'DaysAgo' for i in range(1,nDays+1)]
    #include the y value (supervised (machine) learning)
    dfs.append(newDF[yStr].shift(-1))
    colKeys.append('Tomorrow')
    
    if shift_ns:
        filename = yStr + 'DataShiftNS'+str(nDays)+'.txt'
    else:
        filename = yStr + 'Data' + str(nDays) + '.txt' 
    #drops na, good for supervised training (last day has no y yet
    #and first (nDays-1) days don't have enough data yet)
    pd.concat(dfs,axis=1,keys=colKeys).dropna().astype(int).to_csv(
        filename, index=index, header=header)
    
                   
"""
def predictHazard(colStr):
    
    #predict either SnowHazard or RoadHazard from input
    
    


def predictBothHazards(df):
    
    #"Takes in DataFrame from getStats, ouputs snow and road hazard
    
    
""" 
    
def stormTotal(sNewSnow):
    
    """Count storm totals, infer missing days with linear interpolation
    
    sNewSnow does use timeseries dates parsed properly, from getStats
    
    storm total is aligned with final day of snowfall within the storm
    in input dates (index)
    
    Argument:
    sNewSnow: pandas Series for new snow
    
    Return:
    total storm snow fall aligned with last day of storm
    
    """
    
    
    #assume linear interpolation (better way would be to get historic data)
    interpNewSnow=sNewSnow.asfreq(freq='D').interpolate().int()

    endDays = []
    nextDays = []
    ydy = sNewSnow.index[0]
    for tdy in sNewSnow.index:

        ns = sNewSnow[tdy]
        nsY = sNewSnow[ydy]
        if (ns == 0 or tdy == sNewSnow.index[-1]) and nsY != 0:
            endDays.append(ydy)
            nextDays.append(tdy)
        
        ydy = tdy
    
    #create a series of zeros
    stormTotals = Series(0,index=sNewSnow.index)
    sd = stormTotals.index[0]
    for i, d in enumerate(endDays):
        nd = nextDays[i]
        stormTotals[d] = int(sum(interpNewSnow[sd:nd]))
        
        sd = nd
    
    return stormTotals



def interpDFCols(df,cols=['NewBaseSnow','Temp','SnowHazard','RoadHazard'],
                 rtn_interp=True):
    
    """Returns dataframe filled and interpolated with missing days
    
        Arguments:
        df: dataframe containing at least cols
        
        cols=['NewBaseSnow','Temp','SnowHazard','RoadHazard']
        Columns to interpolate
        
        rtn_interp=True:
        If True, return ONLY the interpolated columns
        If False, return ALL columns, including the interpolated cols
        
        Return:
        df, depends on rtn_interp value
    """
    if rtn_interp:
        #return ONLY the interpolated columns
        return df.loc[:,cols].asfreq(freq='D').interpolate().astype(int)
        
    else:
        df.loc[:,cols] = df.loc[:,cols
                                ].asfreq(freq='D').interpolate().astype(int)
    
        return df


def shiftDFCols(df,shiftCols=['NewBaseSnow','NewPeakSnow'],n_shift=-1,
                rtn_interp=False):
    
    """Return time-indexed dataframe with time-shifted columns
    
        Checks that all shiftCols are in cols
    
        Arguments:
        df: dataframe with time series index
        
        shiftCols=shiftCols=['NewBaseSnow','NewPeakSnow']:
        columns to shift in time by n_shift
        
        n_shift=-1:
        number of index values to shift by (negative means back or up)
                
        rtn_interp=False:
        If True, return ONLY the shifted columns
        If False, return ALL columns, including the shifted cols
    """    
    
    cols = df.columns.tolist()
    
    df=interpDFCols(df,rtn_interp=False)

    #get indices of shiftCols in cols
    for c in shiftCols:
        try:
            #I don't need the index
            cols.index(c)
        except ValueError:
            #c not in cols
            shiftCols.remove(c)
    
    if rtn_interp:
        #return only the interpolated columns
        return df[shiftCols].shift(n_shift)
        
    else:
        df.loc[:,shiftCols] = df.loc[:,shiftCols].shift(n_shift)

        return df
   

def appendBreakNum(df,sentcol='NewBaseSnow',newcol='SnowBreak'):
    
    """Returns dataframe with columns counting which the breaks between snow
    
    A day with new snow is marked with a -1, the others begin at 0
    
    #Note: this allows you to use groupby:
    
    df.groupby('SnowBreak').get_group(1)
    
    for i in range(df['SnowBreak'].min(),df['SnowBreak'].max()):
        print(i,df.groupby('SnowBreak').get_group(i))
    
    """
    #add timedelta as column
    sentval = 0
    n_sent = 0
    
    #initialize
    df=pd.concat([df,DataFrame(data={newcol:n_sent},index=df.index)],
                  axis=1
                  )
    n_bk = 0
    ydy=df.index[0]
    for tdy in df.index:
        if df.loc[tdy,sentcol] == sentval:
            if df.loc[ydy,sentcol] != sentval:
                n_bk += 1
            df.loc[tdy,newcol] = n_bk
        else:
            if df.loc[ydy,sentcol] == sentval:
                n_sent -= 1
            df.loc[tdy,newcol] = n_sent

            
        ydy=tdy
               
    return df
    

def plotHazardsByBreak(gpbyObj):

    fig,ax=plt.subplots(nrows=2,ncols=1)

    ax[0].set_ylim([0,6])
    hs=['SnowHazard','RoadHazard']
    ax[0].set_ylabel(hs[0])
    ax[0].set_xlabel('Days after Snow')
    
    ax[1].set_ylim([0,5])
    ax[1].set_ylabel(hs[1])
    ax[1].set_xlabel('Days after Snow')
    
    for i,h in enumerate(hs):
        for j in range(7,12):
            ax[i].plot(gpbyObj.get_group(j)[h].reset_index(drop=True),
                     marker='o')#label='Break '+str(j))
            #ax[i].legend(loc='best',fontsize=10)
    
    plt.tight_layout(h_pad=0.0)
    #plt.show()
    plt.savefig('hazardDecay7-11.pdf')
            
        
    
def plotStats(df, subplots=True, text=None):

    """Plot arizona snowbowl stats from dataframe

    df can be passed by getStats from azSnowBowlStats.csv

    subplots : default True - splits data into 3 subplots by y units
    text : default False

    """

    if not subplots:
        #return just one subplot
        fig,ax = plt.subplots()
        
        ax.set_ylabel('Inches, Degrees F, Number')
        df[['MinDepth','MaxDepth','NewBaseSnow','NewPeakSnow',
            'Temp','OpenLifts','OpenTrails','SnowHazard',
            'RoadHazard'
            ]].plot(ax=ax,rot=30)

        """
        #set box to 80% height
        #replaced by subplots_adjust
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width, box.height*0.8])
        """
        if text is not None:
            [x, y, s] = text
            ax.text(x,y,s)

        ax.legend(bbox_to_anchor=(0., 1.02, 1.,
            .102),loc=3,ncol=2, mode="expand", borderaxespad=0.)
        
        plt.tight_layout()
        #adjust tight layout for legend (not done with command)
        fig.subplots_adjust(top=0.75)
        
        
    else:
        fig, axes = plt.subplots(nrows=4,ncols=1)

        axes[0].set_ylabel('Inches')
        axes[1].set_ylabel('Hazard Level')
        axes[2].set_ylabel('Number')
        #plt.rc('text',usetex=True)        
        #latex in label r'dsjklsdjk', failed: may be latex problem
        axes[3].set_ylabel('Degrees F')
        

        axes[0] = df[['MinDepth','MaxDepth','NewBaseSnow',
            'NewPeakSnow']].plot(ax=axes[0])
        axes[1] = df[['SnowHazard','RoadHazard']].plot(ax=axes[1],ylim=[0,6])
        axes[2] = df[['OpenLifts','OpenTrails']].plot(ax=axes[2],ylim=[0,47])
        axes[3] = df[['Temp']].plot(ax=axes[3],rot=20)
        
        for i in range(3):
            axes[i].tick_params(
                axis='x',          # changes apply to the x-axis
                which='both',      # both major and minor ticks are affected
                labelbottom='off')
            axes[i].set_xlabel('',visible=False)
        
        for ax in axes:
            """
            #set box to 70% width for outside legend - replaced
            #replaced by subplots_adjust
            box = ax.get_position()
            ax.set_position([box.x0, box.y0, box.width*0.7, box.height])
            """
            if text is not None:
                [x, y, s] = text
                ax.text(x,y,s)
            #bbox_to_anchor=(x_pos of loc,y_pos of loc, x_backgnd width,?)
            ax.xaxis.grid(True)
            ax.yaxis.grid(True)
            ax.legend(bbox_to_anchor=(1.02,1.,
            0.5,0.),loc=2,ncol=1, mode="expand", borderaxespad=0.)
    
        plt.tight_layout(h_pad=0.0)
        #adjust tight layout for legend (not done with command)
        fig.subplots_adjust(right=0.67)
    
    
    plt.show()
    

 

def main():


    [stats,keys] = getConditions()

    [lifts,trails] = getLiftsTrails()
    
    keys.insert(7,'OpenLifts')
    keys.insert(8,'Lifts')
    keys.insert(9,'OpenTrails')
    keys.insert(10,'Trails')

    [stats[keys[7]],stats[keys[8]]] = getNOpen(lifts)
    [stats[keys[9]],stats[keys[10]]] = getNOpen(trails)
    
    #Loop ended
    filename = 'azSnowBowlStats.csv'
    isFile = os.path.isfile('./'+filename)
    with open(filename, 'a') as f:
        
        if not isFile:
            f.write(','.join(keys)+'\n')
        
        ordered_stats = [stats[k] for k in keys]
        f.write(str(list(ordered_stats)).replace(', ',',').strip('[]')+'\n')
        
    print(','.join(keys))
    print(repr(ordered_stats).replace(', ',',').strip('[]'))
        
if __name__ == '__main__':
    main()
