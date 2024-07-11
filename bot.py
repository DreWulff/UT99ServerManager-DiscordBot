# bot.py
import os
import random
import subprocess
import public_ip as ip
import glob # Library for regular expressions in file names
import fileinput
import sys

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from discord.app_commands import Choice

# .env variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
INI_FILE = os.getenv('INI_FILE_NAME')

# Variables for UT99 server management
SV = None
SV_STATUS = False
SV_CMD_PREFIX = '\..\System/ucc.exe" '
SV_CMD_RUN = 'server {map}?game={mode} ini={ini} log=server1.log'
SV_MODE = {
    'DeathMatch': 'BotPack.DeathMatchPlus',
    'TeamDeathMatch': 'BotPack.TeamGamePlus',
    'CaptureTheFlag': 'BotPack.CTFGame',
    'Domination': 'BotPack.Domination',
    'Assault': 'BotPack.Assault',
    'LastManStanding': 'BotPack.LastManStanding',
    'GunGame': 'GunGame.GunGame',
    'MonsterHunt': 'MonsterHunt.MonsterHunt',
    'MonsterArena': 'MonsterHunt.MonsterHuntArena',
    'MonsterDefence': 'MonsterHunt.MonsterHuntDefence'
}
SV_MAPS = {
    'DeathMatch': 'DM',
    'TeamDeathMatch': 'DM',
    'CaptureTheFlag': 'CTF',
    'Domination': 'DOM',
    'Assault': 'AS',
    'LastManStanding': 'DM',
    'GunGame': 'DM',
    'MonsterHunt': 'MH',
    'MonsterArena': 'MA',
    'MonsterDefence': 'CTF'
}
BOT_PATH = os.path.dirname(os.path.realpath(__file__))

INTENTS = discord.Intents.default()
INTENTS.message_content = True
BOT = commands.Bot(command_prefix="!", intents=INTENTS)

async def get_maps (mode):
    """
    Returns the list of maps of a certain mode.
    """
    maps = glob.glob('{path}\..\Maps\{mode}-*.unr'.format(path=BOT_PATH,
                                                        mode=SV_MAPS[mode]))
    
    maps = [map_path.split('\\')[-1].split('.')[0] for map_path in maps]
    return maps

async def get_map_choices (mode):
    """
    Returns the list of maps of a certain mode as Discord choices.
    """
    maps = await get_maps(mode)
    maps = [discord.app_commands.Choice(name=map_name, value=map_name) for map_name in maps]
    return maps[:25]

async def get_modes():
    """
    Returns the available modes for the current version of the game as Discord choices.
    """
    modes = [
        discord.app_commands.Choice(name="DeathMatch", value="DeathMatch"),
        discord.app_commands.Choice(name="Team DeathMatch", value="TeamDeathMatch"),
        discord.app_commands.Choice(name="CTF", value="CaptureTheFlag"),
        discord.app_commands.Choice(name="Assault", value="Assault"),
        discord.app_commands.Choice(name="Domination", value="Domination"),
        discord.app_commands.Choice(name="Last Man Standing", value="LastManStanding")
    ]
    if (os.path.isfile(BOT_PATH + "\..\System\MonsterHunt.u")):
        modes.extend([
            discord.app_commands.Choice(name="Monster Hunt", value="MonsterHunt"),
            discord.app_commands.Choice(name="Monster Arena", value="MonsterArena"),
            discord.app_commands.Choice(name="Monster Defence", value="MonsterDefence")
        ])
    if (os.path.isfile(BOT_PATH + "\..\System\GunGame.u")):
        modes.append(discord.app_commands.Choice(name="Gun Game", value="GunGame"))
    return modes

@BOT.event
async def on_ready():
    try:
        synced = await BOT.tree.sync()
        print(f"Synced {len(synced)} commands(s).")
    except Exception as exception:
        print(exception)

@app_commands.describe(mode="Choose the gamemode. Map will be selected randomly.",
                       players="Bots will fill server if there are less than the desired amount of players.",
                       map_name="Starting map of the server. Optional.")
@BOT.tree.command(name="run", description="Starts a UT99 server with the specified gamemode")
async def run(interaction: discord.Interaction, mode: str, players: int, map_name: str = "Random"):
    global SV
    global SV_STATUS
    if (not SV_STATUS):
        SV_STATUS = True
        sv_mode = SV_MODE[mode]
        config_file = INI_FILE

        # Get desired map, or random by default
        maps = await get_maps(mode)
        map_file = map_name
        if (map_name == "Random"):
            rand_index = random.randrange(len(maps))
            map_file = maps[rand_index]

        # Edit .ini file to define number of bots
        if (mode in ("MonsterHunt", "MonsterArena", "MonsterDefence")):
            config_file = 'MonsterHunt.ini'
        for line in fileinput.input(BOT_PATH + '\\..\\System\\' + config_file, inplace=True):
            if line.strip().startswith('MinPlayers='):
                line = 'MinPlayers={min}\n'.format(min=players)
            sys.stdout.write(line)

        command = '"' + BOT_PATH + SV_CMD_PREFIX + SV_CMD_RUN.format(map=map_file, mode=sv_mode, ini=INI_FILE)
        print(command)
        SV = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=None, stderr=None, close_fds=True, encoding='utf8', creationflags=subprocess.CREATE_NEW_CONSOLE)
        await interaction.response.send_message("UT server online! Use **/join** for instructions on how to join")
        await BOT.change_presence(activity=discord.Game(name=mode))
    else:
        await interaction.response.send_message("UT99 server already online!", ephemeral=True)
@run.autocomplete("mode")
async def autocomplete_mode(
    interaction: discord.Interaction,
    current: str):
    return await get_modes()
@run.autocomplete("map_name")
async def autocomplete_map(
    interaction: discord.Interaction,
    current: str):
    return await get_map_choices(interaction.namespace.mode)


@BOT.tree.command(name="maps", description="Shows a list of maps for given mode")
async def maps(interaction: discord.Interaction, mode: str):
    maps = await get_maps(mode)
    message = ''
    for mapfile in maps:
        message += '* ' + mapfile + '\n'
    map_choices = await get_map_choices(interaction.namespace.mode)
    print(map_choices)
    await interaction.response.send_message(message, ephemeral=True)
@maps.autocomplete("mode")
async def autocomplete_mode(
    interaction: discord.Interaction,
    current: str):
    return await get_modes()

@BOT.tree.command(name="stop", description="Forcefully stops the UT99 server")
async def stop(interaction: discord.Interaction):
    global SV
    global SV_STATUS
    if (not SV_STATUS):
        await interaction.response.send_message("There isn't a UT99 server currently running", ephemeral=True)
    else:
        SV.kill()
        SV_STATUS = False
        await interaction.response.send_message("UT99 server got monstruosly killed!")
        await BOT.change_presence(status=discord.Status.online, activity=None)


@BOT.tree.command(name="join", description="Gives instructions on how to join the UT99 server")
async def join(interaction: discord.Interaction):
    global SV_STATUS
    if (not SV_STATUS):
        await interaction.response.send_message("There isn't a UT99 server currently running", ephemeral=True)
    else:
        await interaction.response.send_message("Connect to **" + ip.get() + ":7777** through Multiplayer option 'Open Location'", ephemeral=True)


@BOT.tree.command(name="help", description="Give a list of the available commands")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message("**run**: Starts a UT99 server with the specified game mode\n"+
                                            "**stop**: Forcefully stops the UT99 server\n"+
                                            "**joke**: Eat that!\n"+
                                            "**get game**: Get the game's download link and installation instructions",
                                            ephemeral=True)


BOT.run(TOKEN)