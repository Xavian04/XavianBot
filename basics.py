import json
import urllib.request
import shared_info
from difflib import SequenceMatcher
import random
import asyncio
import aiohttp
import aiofiles
import os
import subprocess
from io import BytesIO
import discord

bot = shared_info.bot


def clean_priorities(db):
    for n, s in db.items():
        offers = s['offers']
        offers = sorted(offers, key=lambda o: o['priority'])
        teams = []
        for o in offers:
            teams.append(o['team'])
        teams = set(teams)
        teams = list(teams)
        for t in teams:
            pri = 1
            for o in offers:
                if o['team'] == t:
                    o['priority'] = pri
                    pri += 1
    return db





async def save_db_content(db, name='servers.json'):
    if name == 'servers.json':
        db = clean_priorities(db)
    async with aiofiles.open(name, 'w') as f:
        await f.write(json.dumps(db))

async def save_db(db, name='servers.json'):
    await asyncio.create_task(save_db_content(db, name))

def load_db(name='servers.json'):
    with open(name) as f:
        db = json.load(f)
    return(db)

import dropbox
'''async def update_export_content(text, message):
    await message.channel.send('Uploading your export to dropbox...')
    """
    Uploads a file to Dropbox and returns a shareable link.
    
    :param file_path: Local path to the file to be uploaded.
    :param dest_path: Path in Dropbox where the file will be saved.
    :param access_token: OAuth2 access token for Dropbox.
    :return: Shareable link to the uploaded file.
    """

    dbx = dropbox.Dropbox('sl.BkTycYdhS78YOOIFgA0XPEMjLLbpB93m395Ew8GMx0hSIhZgca-dGjYpEW5xXzv0dU9XsSIQtG1moAHXCtOZEqFfPcYboYmL9u5hpgVRO75rx7kEotAb5s0nOkYtsY9Gz8ViXQI96MGvJt-kr7wPBEY')

    current_dir = os.getcwd()
    path_to_file = os.path.join(current_dir, "exports", f"{message.guild.id}-export.json")
    # Upload the file
    with open(path_to_file, "rb") as f:
        dbx.files_upload(f.read(), f'/exports/{message.guild.id}-export.json')


    # Get a shareable link

    try:
        shared_link_metadata = dbx.sharing_create_shared_link_with_settings(f'/exports/{message.guild.id}-export.json')
        url = shared_link_metadata.url
    except dropbox.exceptions.ApiError as e:
        # If a shared link already exists, get the existing link
        if isinstance(e.error, dropbox.sharing.CreateSharedLinkWithSettingsError) and \
           e.error.is_shared_link_already_exists():
            links = dbx.sharing_list_shared_links(path=f'/exports/{message.guild.id}-export.json').links
            if len(links) > 0:
                url = links[0].url


    
    text = '**Your dropbox link:** ' + url.replace('www.', 'dl.')
    await message.channel.send(text)

async def update_export(text, message):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, update_export_content, text, message)'''

# Your initial tokens and app credentials
#ACCESS_TOKEN = 'sl.BkZdtVI-xXLGxM1ZB75qUVbvVVWLMORv-_9oLShKTq5qzuGTNTCmUWVurK_KLSDM2ii2_eQaJaHrGRAMEpytjKT3jQF6JFV-bHGSuEQs7r2LJI9UOWz8S_jAwRtcCAJz2-kTA2b6h0cAiqyiIfv-NRI'
ACCESS_TOKEN = 'Obviously incorrect access token'
REFRESH_TOKEN = 'AlO_XX6jdbsAAAAAAAAAAWzjYQWG0ZkHOlV97coSR7oDeHsByAmfRPy0vvyfFdzC'
CLIENT_ID = '21dxpzehtthns20'
CLIENT_SECRET = '7jr9aug3g1un2li'

def refresh_access_token():
    global ACCESS_TOKEN, REFRESH_TOKEN
    flow = dropbox.DropboxOAuth2FlowNoRedirect(CLIENT_ID, CLIENT_SECRET, token_access_type='offline')
    print(flow)
    print(flow.start())
    dbx = dropbox.Dropbox(oauth2_refresh_token=REFRESH_TOKEN, app_key=CLIENT_ID, app_secret = CLIENT_SECRET)
    return dbx
        #dbx.users_get_current_account()
        #print("Successfully set up client!")
    #new_tokens = flow.refresh_access_token(REFRESH_TOKEN)
    #ACCESS_TOKEN = new_tokens.access_token
    #REFRESH_TOKEN = new_tokens.refresh_token

def upload_to_dropbox(path_to_file, dest_path):
    global ACCESS_TOKEN
    CHUNK_SIZE = 4 * 1024 * 1024
    dbx = dropbox.Dropbox(ACCESS_TOKEN)

    # Check if the file already exists
    try:
        dbx.files_get_metadata(dest_path)
        dbx.files_delete_v2(dest_path)
    except dropbox.exceptions.AuthError as e:
        dbx = refresh_access_token()
        try:
            dbx.files_get_metadata(dest_path)
            dbx.files_delete_v2(dest_path)
        except dropbox.exceptions.ApiError as e:
            if not (isinstance(e.error, dropbox.files.GetMetadataError) and e.error.is_path()):
                raise

    with open(path_to_file, "rb") as f:
        file_size = os.path.getsize(path_to_file)

        if file_size <= CHUNK_SIZE:
            dbx.files_upload(f.read(), dest_path)
        else:
            upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
            session_id = upload_session_start_result.session_id
            offset = CHUNK_SIZE

            while offset < file_size:
                if file_size - offset <= CHUNK_SIZE:
                    dbx.files_upload_session_finish(f.read(CHUNK_SIZE), dropbox.files.UploadSessionCursor(session_id=session_id, offset=offset), dropbox.files.CommitInfo(path=dest_path))
                else:
                    dbx.files_upload_session_append_v2(f.read(CHUNK_SIZE), dropbox.files.UploadSessionCursor(session_id=session_id, offset=offset))
                offset += CHUNK_SIZE

    try:
        shared_link_metadata = dbx.sharing_create_shared_link_with_settings(dest_path)
        url = shared_link_metadata.url
    except dropbox.exceptions.AuthError as e:
        dbx = refresh_access_token()  
        return upload_to_dropbox(path_to_file, dest_path)
        print("ok")
    except dropbox.exceptions.ApiError as e:
        if isinstance(e.error, dropbox.sharing.CreateSharedLinkWithSettingsError) and e.error.is_shared_link_already_exists():
            links = dbx.sharing_list_shared_links(path=dest_path).links
            if len(links) > 0:
                url = links[0].url

    return url

async def update_export_content(message):
    await message.channel.send('Uploading your export to dropbox...')
    current_dir = os.getcwd()
    path_to_file = os.path.join(current_dir, "exports", f"{message.guild.id}-export.json")
    await save_db(shared_info.serverExports[str(message.guild.id)], path_to_file)
    loop = asyncio.get_event_loop()
    url = await loop.run_in_executor(None, upload_to_dropbox, path_to_file, f"/exports/{message.guild.id}-export.json")
    text = '**Your dropbox link:** ' + url.replace('www.', 'dl.')
    await message.channel.send(text)

async def update_export(text, message):
    print("updating export")
    asyncio.create_task(update_export_content(message))

async def load_export_content(text, message):
    if len(text) == 1:
        await message.channel.send('Please provide an export URL.')
    else:
        url = text[1]
        exportCheck = url.startswith('http')
        if exportCheck:
            await message.channel.send('Loading export...')
            try: 
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        async with aiofiles.open(f'exports/{message.guild.id}-export.json', 'wb') as f:
                            while True:
                                chunk = await response.content.read(1024)
                                if not chunk:
                                    break
                                await f.write(chunk)

                async with aiofiles.open(f'exports/{message.guild.id}-export.json', 'r') as f:
                    data = await f.read()
                data = json.loads(data)
                shared_info.serverExports[str(message.guild.id)] = data
                #brief initialization on exports
                players = shared_info.serverExports[str(message.guild.id)]['players']
                for p in players:
                    p['stats'].sort(key=lambda s: s['season'])
                    p['ratings'].sort(key=lambda r: r['season'])
                await message.channel.send('Complete!')
            except Exception as e:
                print(f"An error: {e}") 
                await message.channel.send("There was an error loading that file. Ensure it's a valid JSON or try another link.")
        else:
            await message.channel.send('Invalid link.')

async def load_export(text, message):
    print("loading")
    loop = asyncio.get_event_loop()
    await loop.create_task(load_export_content(text, message))

def find_match(input, export, fa=False, activeOnly=False):
    bestMatch = 0
    players = export['players']
    for p in players:
        p['tid'] = int(p['tid'])
        playerName = p['firstName'] + ' ' + p['lastName']
        matchScore = SequenceMatcher(a=str.lower(input), b=str.lower(playerName.replace('.', '')))
        matchScore = float(matchScore.ratio())
        if p['ratings'][-1]['ovr'] > 50:
            matchScore += (random.randint(7500,10000))/100000000 #random player if blank input
        else:
            matchScore += (random.randint(1,10000))/100000000 #random player if blank input
        if p['tid'] > -1 or p['tid'] == -2:
            matchScore += 0.1
            if export['gameAttributes']['phase'] == 5:
                if p['tid'] == -2:
                    matchScore += 0.15
        #adding later for FA
        if fa:
            if p['tid'] == -1:
                matchScore += 0.5
        if activeOnly:
            if p['tid'] > -2:
                matchScore += 0.5
        if input.replace(' ', '') == playerName.replace(' ', ''):
            matchScore += 1
        if ' ' + str.lower(p['firstName']) + ' ' in str.lower(input + ' '):
            matchScore += p['ratings'][-1]['ovr']/250
            matchScore += 0.33
        if ' ' + str.lower(p['lastName'].replace('.', '')) + ' ' in str.lower(input + ' '):
            matchScore += p['ratings'][-1]['ovr']/250
            matchScore += 0.33
        if matchScore > bestMatch:
            bestMatch = matchScore
            winningPlayer = p['pid']
    return winningPlayer

def group_numbers(numbers):
    if numbers == []:
        return 'No Experience'
    else:
        numbers.sort()
        groups = []
        start = numbers[0]
        end = numbers[0]
        for i in range(1, len(numbers)):
            if numbers[i] == end + 1:
                end = numbers[i]
            else:
                if start == end:
                    groups.append(str(start))
                else:
                    groups.append(str(start) + '-' + str(end))
                start = numbers[i]
                end = numbers[i]
        if start == end:
            groups.append(str(start))
        else:
            groups.append(str(start) + '-' + str(end))
        return ', '.join(groups)

def rating_names(text):
    text = str.lower(text)
    ratingTerms = {
        "hgt": ['height', 'tall', 'tallness', 'size', 'stature',],
        "stre": ['strength', 'muscle', 'toughness', 'fat', 'big', 'heavy', 'wide'],
        "spd": ['speed', 'quick', 'quickness', 'rapidity', 'velocity', 'agility', 'acceleration'],
        "jmp": ['jump', 'jumping', 'vertical', 'leap', 'leaping', 'bounce', 'hop'],
        "endu": ['endurance', 'stamina', 'cardio', 'resilience', 'sustainability'],
        "ins": ['inside', 'post', 'interior', 'paint', 'lowpost', 'closerange'],
        "dnk": ['dunks', 'layups', 'dunks/layups', 'slashing', 'driving', 'finishing'],
        "ft": ['freethrows', 'freethrow', 'foulshot', 'free'],
        "fg": ['midrange', '2pt', 'twopoint', 'twopointers', 'two', '2p'],
        "tp": ['threepoint', 'outside', 'range', '3pt', 'three', 'triple', '3p'],
        "oiq": ['offensiveiq', 'offense', 'offensiveawareness'],
        "diq": ['defensiveiq', 'defense', 'defensiveawareness'],
        "drb": ['dribbling', 'handling', 'handles', 'control', 'ballhandling'],
        "pss": ['passing', 'pass', 'playmaking', 'pas', 'assist'],
        "reb": ['rebounding', 'boards', 'board', 'rebound', 'boxout', 'box']
    }
    for r, t in ratingTerms.items():   
        for thing in t:
            if text == thing:
                text = r
    return text

def get_setting_value(setting, export, year=None):
    settingData = export['gameAttributes'][setting]
    if year == None:
        year = export['gameAttributes']['season']
    value = None
    if isinstance(settingData, list):
        if isinstance(settingData[0], dict):
            for s in settingData:
                if s['start'] <= int(year):
                    value = s['value']
        else:
            value = settingData
    else: value = settingData
    return value


def find_pick_info(text, export):
    text = str.lower(text)
    #say for instance '2121 2nd round pick (NYC)'
    #find the round
    pickData = {
        "round": None,
        "year": None,
        "tid": None
    }
    roundTerms = {
        1: ['first', '1st', 'round 1', ' 1 round', 'rd 1', ' 1 rd'],
        2: ['second', '2nd', 'round 2', ' 2 round', 'rd 2', ' 2 rd'],
        3: ['third', '3rd', 'round 3', ' 3 round', 'rd 3', ' 3 rd'],
        4: ['fourth', '4th', 'round 4', ' 4 round', 'rd 4', ' 4 rd'],
        5: ['fifth', '5th', 'round 5', ' 5 round', 'rd 5', ' 5 rd'],
        6: ['sixth', '6th', 'round 6', ' 6 round', 'rd 6', ' 6 rd'],
        7: ['seventh', '7th', 'round 7', ' 7 round', 'rd 7', ' 7 rd'],
        8: ['eighth', '8th', 'round 8', ' 8 round', 'rd 8', ' 8 rd'],
        9: ['ninth', '9th', 'round 9', ' 9 round', 'rd 9', ' 9 rd']
    }
    rounds = get_setting_value('numDraftRounds', export)
    if rounds > 9:
        for i in range(10, rounds):
            roundTerms[i] = [str(i), 'round ' + str(i), str(i) + ' round', 'rd ' + str(i), str(i) + ' rd']
    for roundNum, roundTexts in roundTerms.items():
        for txt in roundTexts:
            if txt in text:
                pickData['round'] = roundNum
    #find the year
    for i in range(1000, 3000):
        if ' ' + str(i) + ' ' in text or text.startswith(str(i) + ' '):
            pickData['year'] = i
    #find the team
    teams = export['teams']
    for t in teams:
        if (str.lower(t['abbrev']) in text or str.lower(t['region']) in text or str.lower(t['name']) in text.replace('round', '').replace('pick', '')):
            pickData['tid'] = t['tid']
    return pickData

def calculate_formula(p, season, formula):
    age = season - p['born']['year']
    r = p['ratings'][-1]
    hgt = r['hgt']
    stre = r['stre']
    spd = r['spd']
    jmp = r['jmp']
    endu = r['endu']
    ins = r['ins']
    dnk = r['dnk']
    fg = r['fg']
    ft = r['ft']
    tp = r['tp']
    oiq = r['oiq']
    diq = r['diq']
    drb = r['drb']
    pss = r['pss']
    reb = r['reb']
    ovr = r['ovr']
    pot = r['pot']
    value = eval(formula)
    return value

def formula_ranking(players, season, formula):
    playerList = []
    for p in players:
        value = calculate_formula(p, season, formula)
        playerList.append([p['pid'], value])
    playerList.sort(key=lambda p: p[1], reverse=True)
    
    return playerList

def team_mention(message, teamName, abbrev):
    role = discord.utils.get(message.guild.roles, name=teamName)
    if role is not None:
        roleMention = role.mention
    else:
        # Role does not exist, so just use the team name
        roleMention = teamName
    emoji = discord.utils.get(message.guild.emojis, name=str.lower(abbrev))
    if emoji is not None:
        teamText = f"{roleMention} {emoji}"
    else:
        teamText = roleMention
    return teamText

def rookie_salary(pick, serverExport):
    draftPicks = serverExport['draftPicks']
    players = serverExport['players']
    season = serverExport['gameAttributes']['season']
    totalPicks = 0
    for dpick in draftPicks:
        if dpick['round'] == 1 and dpick['season'] == season:
            totalPicks += 1
    for p in players:
        if p['draft']['year'] == season and p['draft']['round'] == 1:
            totalPicks += 1

    topRookieSalary = (serverExport['gameAttributes']['draftPickAutoContractPercent']/100)*serverExport['gameAttributes']['maxContract']
    minContract = serverExport['gameAttributes']['minContract']
    topThird = round(totalPicks / 3, 0)
    if pick <= topThird:
        salary = (topRookieSalary - minContract)*0.5/(topThird - 1) * (topThird - pick)
        salary = salary + (topRookieSalary - minContract)*0.5 + minContract
        salary = round(salary)
        return salary
    else:
        startPoint = ((topRookieSalary - minContract)*0.5) + minContract
        numPicks = totalPicks - topThird
        salary = (startPoint - minContract)/(numPicks+1) * (totalPicks - pick + 1)
        salary = round(salary + minContract)
        return salary
    
def get_nested_value(dct, keys):
    #Retrieve a value from a nested dictionary using a list of keys.
    for key in keys:
        if key in dct:
            dct = dct[key]
        else:
            return None
    return dct
    
def player_list_embed(playerList, pageNum, season, sortBy, reverse=True, draft=False):
    values = ['ovr', 'pot', 'hgt', 'stre', 'spd', 'jmp', 'endu', 'ins', 'dnk', 'ft', 'fg', 'tp', 'oiq', 'diq', 'drb', 'pss', 'reb']
    if isinstance(sortBy, str):
        sortBy = rating_names(sortBy)
        if str.lower(sortBy) in values:
            sortBy = str.lower(sortBy)
            playerList.sort(key=lambda o: o['ratings'][sortBy], reverse=reverse)
        else:
            sortBy = 'ovr'
    else:

        playerList.sort(key=lambda p: get_nested_value(p, sortBy), reverse=reverse)
    
    totalPages, remainder = divmod(len(playerList), 14)
    totalPages += 1
    playerList = playerList[((pageNum-1)*14):(pageNum*14)]
    commandText = ''
    number = (pageNum-1)*14 + 1
    for f in playerList:
        if draft:
            line = f"- ``R{f['draftRound']} P{f['draftPick']}``. {f['position']} **{f['name']}** - {f['draftYear'] - f['born']} yo {f['draftRating']}"
            if isinstance(sortBy, str):
                line += f": **{f['ratings'][sortBy]} {str.upper(sortBy)}**"
            commandText += line + '\n'
        else:
            

            line = f"- ``{number}``. {f['position']} **{f['name']}** - {season - f['born']} yo {f['ovr']}/{f['pot']} {f['skills']}"
            if isinstance(sortBy, str):
                line += f" **{f['ratings'][sortBy]} {str.upper(sortBy)}**"
            else:
                if sortBy != ['value']:
                    line +=  f": **{get_nested_value(f, sortBy)}**"
            commandText += line + '\n'
            number += 1
    
    commandText += '\n' + f"*{totalPages} total pages.*"
    if isinstance(sortBy, str):
        return [commandText, str.upper(sortBy), totalPages]
    else:
        return [commandText, str(sortBy[-1]), totalPages]

async def resign_odds(playerPrices, years, offerAmount):
    if int(years) in playerPrices:
        askingPrice = playerPrices[int(years)]
        offerRatio = float(offerAmount) / (askingPrice/1000)
        if offerRatio >= 1:
            probability = 1
        else:
            if offerRatio > 0.5:
                probability = ((offerRatio-0.5)/0.5)**2
            else:
                probability = 0
    else:
        probability = 0
    return probability

import copy
async def release_player(pid, message):
    serverId = message.guild.id
    export = shared_info.serverExports[str(serverId)]
    players = export['players']
    events = export['events']
    season = export['gameAttributes']['season']
    teams = export['teams']
    for p in players:
        if p['pid'] == pid:
            playerName = p['firstName'] + ' ' + p['lastName']
            age = season - p['born']['year']
            ovr = p['ratings'][-1]['ovr']
            pot = p['ratings'][-1]['pot']
            tid = copy.deepcopy(p['tid'])
            for t in teams:
                if t['tid'] == tid:
                    abbrev = t['abbrev']
                    teamName = t['region'] + ' ' + t['name']
            newEvent = {
                'type': 'release',
                'pids': [pid],
                'tids': [tid],
                'season': season,
                'eid': events[-1]['eid']+1,
                'text': f'The <a href="/l/20/roster/{abbrev}/{season}">{teamName}</a> released <a href="/l/20/player/{pid}">{playerName}</a>.'
            }
            events.append(newEvent)
            if p['draft']['year'] != season:
                if p['draft']['year'] == season - 1 and export['gameAttributes']['phase'] == 0:
                    p['salaries'] = []
                else:
                    newRelease = {
                        'pid': p['pid'],
                        'tid': tid,
                        'contract': copy.deepcopy(p['contract'])
                    }
                    try: newRelease['rid'] = export['releasedPlayers'][-1]['rid'] + 1
                    except: newRelease['rid'] = 0
                    try: export['releasedPlayers'].append(newRelease)
                    except:
                        export['releasedPlayers'] = []
                        export['releasedPlayers'].append(newRelease)
            else:
                p['salaries'] = []
            p['tid'] = -1
            p['contract']['amount'] == export['gameAttributes']['minContract']
            p['contract']['exp'] = season+1

            text = f">>> **Release** \n -- \n The {team_mention(message, teamName, abbrev)} release **{playerName}** ({age} yo {ovr}/{pot}). \n --"
            channelId = int(shared_info.serversList[str(serverId)]['releasechannel'].replace('<#', '').replace('>', ''))
            channel = shared_info.bot.get_channel(channelId)
            if isinstance(channel, discord.TextChannel):
                # Send the message to the channel
                await channel.send(text)
                current_dir = os.getcwd()
                path_to_file = os.path.join(current_dir, "exports", f"{serverId}-export.json")
                await save_db(export, path_to_file)
            else:
                if errorSent == False:
                    message.channel.send('Your FA channel is invalid, so signings were not sent. FA was still executed.')
                    errorSent = True





    
