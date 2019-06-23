#!/usr/bin/env python

ROOT_LINK = 'https://www.srbijasport.net'
SERBIA_START_PAGE = 'https://www.srbijasport.net/league/3855/games'
MONTENEGRO_START_PAGE = 'https://www.srbijasport.net/league/3861/games'
SERBIA_EXPORT_FILE_NAME = 'serbiaData.csv'
MONTENEGRO_EXPORT_FILE_NAME = 'montenegroData.csv'

ONGOING_SEASON = '2019-2020'
SEASON_CUTOFF = '2005-2006'
LEVEL_CUTOFF = 5

TITLE = [
    'League Name',
    'League Level',
    'League Season',
    'Matchday',
    'Match Date',
    'Match Time',
    'Host Team ID',
    'Host Team Name',
    'Host Team Hometown',
    'Host Team URL',
    'Guest Team ID',
    'Guest Team Name',
    'Guest Team Hometown',
    'Guest Team URL',
    'Goals Host',
    'Goals Guest',
    'Goals Host Half Time',
    'Goals Guest Half Time'
    ]

DRIVER_NAME = 'chromedriver'
