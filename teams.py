import shared_info
exports = shared_info.serverExports
serversList = shared_info.serversList
import basics
import pull_info
from pull_info import tinfo
import discord
import team_commands as tc

##TEAM COMMANDS

commandFuncs = {
    'roster': tc.roster,
    'sroster': tc.roster,
    'psroster': tc.roster,
    'lineup': tc.lineup,
    'picks': tc.picks,
    'ownspicks': tc.ownspicks,
    'history': tc.history,
    'finances': tc.finances,
    'seasons': tc.seasons,
    'tstats': tc.tstats,
    'ptstats': tc.tstats,
    'sos': tc.sos,
    'schedule': tc.schedule,
    'gamelog': tc.gamelog,
    'game': tc.game,
    'boxscore': tc.boxscore
}


async def process_text(text, message):
    export = exports[str(message.guild.id)]
    season = export['gameAttributes']['season']
    players = export['players']
    teams = export['teams']
    commandSeason = season
    command = str.lower(text[0])
    for m in text:
        try:
            m = int(m)
            commandSeason = m
            text.remove(str(commandSeason))
        except:
            pass
    
    #default the command team to the user team, then search if a team was specified
    try: commandTid = serversList[str(message.guild.id)]['teamlist'][str(message.author.id)]
    except KeyError: commandTid = -1
    practicalSeason = commandSeason
    if command in ['game', 'boxscore']:
        practicalSeason = season
    if practicalSeason != season:
        for t in teams:
            seasons = t['seasons']
            for s in seasons:
                if s['season'] == practicalSeason:
                    teamNames = [s['abbrev'], s['region'], s['name'], s['region'] + ' ' + s['name']]
                    for name in teamNames:
                        if str.lower(name) in [str(m).lower() for m in text]:
                            commandTid = t['tid']
        if commandTid == -1:
            for t in teams:
                teamNames = [t['abbrev'], t['region'], t['name'], t['region'] + ' ' + t['name']]
                for name in teamNames:
                    if str.lower(name) in [str(m).lower() for m in text]:
                        commandTid = t['tid']
    else:
        for t in teams:
            teamNames = [t['abbrev'], t['region'], t['name'], t['region'] + ' ' + t['name']]
            for name in teamNames:
                if str.lower(name) in [str(m).lower() for m in text]:
                    commandTid = t['tid']
    found = False
    for team in teams:
        if team['tid'] == int(commandTid):
            found = True
            t = pull_info.tinfo(team, practicalSeason)
    
    if found == False:
        await message.channel.send('No team found. Please specify a team.')
    else:

        descriptionLine = f"{practicalSeason}: {t['record']} record, {pull_info.playoff_result(t['roundsWon'], export['gameAttributes']['numGamesPlayoffSeries'], commandSeason, True)}"
        if descriptionLine[-2:] == ', ':
            descriptionLine = descriptionLine[:-2]
        embed = discord.Embed(title=t['name'], description=descriptionLine, color=t['color'])

        #pull together some essential command info to pass along to the command funcs
        commandInfo = {"serverId": message.guild.id,
                    "season": commandSeason,
                    "command": command,
                    "message": message}
        #uncomment to get a full error message in console
        #embed = commandFuncs[command](embed, t, commandInfo) 
        try: embed = commandFuncs[command](embed, t, commandInfo) #fill the embed with the specified function
        except Exception as e:
            print(e) 
            embed.add_field(name='Error', value="An error occured. Command may not be specified.", inline=False)
        
        #add the bottom parts
        embed.set_footer(text=shared_info.embedFooter)
        await message.channel.send(embed=embed)



