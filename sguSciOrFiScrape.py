# -*- coding: utf-8 -*-
"""
Search through:
http://theskepticsguide.org/podcast/sgu/#
where # is the podcast number without zero padding
to find science or fiction content

Uses BeautifulSoup and urllib

Print science or fiction items either to the screen or to a csv file
named: scienceOrFiction.csv
format:
EpNum, ItemNum, SciOrFi, Prompt

with the header for the first column containing the base url for 
the podcast show notes page:
http://theskepticsguide.org/podcast/sgu/

Note, if you wish to load this into a relational database, the first 2 
columns/fields form a composite key
"""
from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
import os.path

'''
Input: url to the SGU show notes page for a particular episode, and
    text (lowercase) you want to find within a string inside the segment
Output: a node in a BeautifulSoup html-parsed tree to the matching 
    podcast segment
    
'''
def getSegmentWith(sguEpUrl, loweredText):
    
    soup = BeautifulSoup(urlopen(sguEpUrl),'lxml')
    #use 'html5lib' if you need nodes to have the .descendants member
    
    segs = soup.find(class_='podcast-segments')
    #find feature does not work to search for 'Science or Fiction'
    
    theSegment = None
    for seg in segs.find_all(class_='podcast-segment'):
        for string in seg.stripped_strings:
            if loweredText in string.lower():
                theSegment = seg
    
    return theSegment

'''
Input: theSegment you want to pull text from under podcast-item-value
Output: list of text for all podcast-item-values
'''
def getSegmentTexts(theSegment):
    
    segTexts = []    
    
    for segVal in theSegment.find_all(class_='podcast-item-value'):
        for string in segVal.stripped_strings:
            segTexts.append(string)
        
    return segTexts

'''
Input: BeautifulSoup node for science of fiction podcast-segment
Output: list of science or fiction items, whether they are 
    'science' or 'fiction'
'''
def getSciFiAnswers(theSegment):

    sciFiAnswers = []
    for ans in theSegment.find_all(class_=re.compile('sciFiAnswers')):
        for string in ans.stripped_strings:
            sciFiAnswers.append(string.lower())
        
    return sciFiAnswers

def main():
    
    aOrw = 'a'
    print2Screen = True
    if not print2Screen:
        print2CSV = True
    else:
        print2CSV = False
    
    sguArv = 'http://theskepticsguide.org/podcast/sgu/'
    
    #first episode with Science or Fiction is 3
    #some episodes do not have it listed: be sure it handles those
    epBeg = 29
    #epEnd = 30
    epEnd = epBeg+5    

    if print2CSV:
        fileName = 'scienceOrFictions.csv'
        #Choose whether to write a header
        if os.path.isfile(fileName) and aOrw == 'a':
            f=open(fileName,aOrw)
            #ending gets truncated
            f.write('\n')
        else:
            f=open(fileName,aOrw)
            line = ('"http://theskepticsguide.org/podcast/sgu/"'
                ',"ItemNum","SciOrFi","Prompt"\n')
            f.write(line)
    
    for epNum in range(epBeg,epEnd+1):
        
        sguEpUrl = sguArv+str(epNum)
        sciFiSegment = getSegmentWith(sguEpUrl, 'science or fiction')
        #print(sciFiSegment.prettify())        
        
        if sciFiSegment is not None:
            sciFiItems = getSegmentTexts(sciFiSegment)
            sciFiAnswers = getSciFiAnswers(sciFiSegment)
        
        #Print items either to screen or to a csv file, format:
        # epNum, ItemNum, SciOrFi, Prompt
        if print2Screen and (sciFiSegment is not None):
            print(sguEpUrl)
            print('Science or Fiction')
            for i,item in enumerate(sciFiItems):
                print('Item',i+1,':',sciFiAnswers[i])
                print(item,'\n')
        elif print2CSV and (sciFiSegment is not None):
            for i,item in enumerate(sciFiItems):
                sciOrFi = sciFiAnswers[i]
                line = ('"'+str(epNum)+'","'+
                        str(i+1)+'","'+sciOrFi+'","'+item+'"\n')
                f.write(line)
    #after all episodes printed
    if print2CSV:
        f.close()

if __name__ == '__main__':
    main()