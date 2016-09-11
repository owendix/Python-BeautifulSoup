# -*- coding: utf-8 -*-
"""
Search through:
http://theskepticsguide.org/podcast/sgu/
then 
http://theskepticsguide.org/podcast/sgu/#
where # is the podcast number without zero padding
to find content name that logical fallacy content


Print science or fiction items either to the screen or to a csv file
named: nameLogicalFallacies.csv
format:
Episode, Prompt

with the header for the first column containing the base url for 
the podcast show notes page:
http://theskepticsguide.org/podcast/sgu/

Note, if you wish to load this into a relational database, the first
column/field should be unique
"""
from urllib.request import urlopen
import bs4
from bs4 import BeautifulSoup
import re
import os.path

'''
Input: lower case text saying what you want to have in the episode
Output: list of episodes (name and date, with text) which include that lower-
    case text
'''
def getEpisodesWith(loweredText):
    sguArv = 'http://theskepticsguide.org/podcast/sgu/'
    soup = BeautifulSoup(urlopen(sguArv),'lxml')
    
    #find podcasts-description
    descripts = soup.find_all(class_='podcasts-description')
    
    epList = []    
    
    #search for 'name that logical fallacy'
    for descr in descripts:
        for string in descr.stripped_strings:
            if loweredText in string.lower():
                #if found go up to podcasts-number
                for ep \
                in descr.previous_sibling.previous_sibling.stripped_strings:
                    epList.append(getEpNumber(ep))
    
    return epList
    
'''
Input: episode Number and Date with text string, an epList element
    Format: Episode #epNum - Date
Output: episode number from text
'''
def getEpNumber(epTitle):
    return re.compile('#[0-9]*').findall(epTitle)[0][1:]

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
    
def main():
    
    aOrw='a'
    print2Screen = False
    if not print2Screen:
        print2CSV = True
    else:
        print2CSV = False
    
    sguArv = 'http://theskepticsguide.org/podcast/sgu/'

    if print2CSV:
        fileName = 'nameLogicalFallacies.csv'
        #Choose whether to write a header
        if os.path.isfile(fileName) and aOrw == 'a':
            f=open(fileName,aOrw)
            #ending gets truncated
            f.write('\n')
        else:
            f=open(fileName,aOrw)
            line = ('"http://theskepticsguide.org/podcast/sgu/","Text"'
                    ',"BestFallacies","CloseFallacies"\n')
            f.write(line)
    
    #text needs to be lowercase
    epNums = getEpisodesWith('name that logical fallacy')
    #print(epNums)
    '''['522', '499', '486', '459', '456', '452', '445', '436', '431', '422', 
    '419', '396', '391', '369', '361', '349', '339', '329', '325', '320', 
    '292', '290', '287', '280', '272', '257', '247', '245', '239', '237', 
    '235', '212', '192', '176', '168', '165', '152', '132', '124', '121', 
    '113', '107', '102', '98', '92', '89', '86', '85', '65', '64', '63', '60', 
    '59', '56', '53', '49', '45', '43', '41'] (41 no notes)'''
    
    #so I don't overload them until I have permission
    #epNums = ['64', '63', '60','59', '56','53', '49', '45', '43', '41']
    beg = 50
    for epNum in epNums[beg:]:
        
        sguEpUrl = sguArv+str(epNum)
        nlfSegment = getSegmentWith(sguEpUrl, 
                                          'name that logical fallacy')
        #print(sciFiSegment.prettify())        
        
        if nlfSegment is not None:
            #returns a list of texts, should only be one entry [0]
            nlfTexts = getSegmentTexts(nlfSegment)
            #some may have separator tags <br>, this concatenates
            nlfText = ' '.join(nlfTexts)
        
        #Print items either to screen or to a csv file, format:
        # epNum, ItemNum, SciOrFi, Prompt
        if print2Screen and (nlfSegment is not None):
            print(sguEpUrl)
            print('Name That Logical Fallacy')
            print(nlfText)
        elif print2CSV and (nlfSegment is not None):
            line = ('"'+str(epNum)+'","'+nlfText+'"\n')
            f.write(line)
    #after all episodes printed
    if print2CSV:
        f.close()

if __name__ == '__main__':
    main()