# bot.py
# Python libraries
import os
import random
import subprocess
import glob
import fileinput
import sys

# External libraries
from dotenv import load_dotenv
import public_ip as ip  # Used for /join command
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.app_commands import Choice

# .env variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
INI_FILE = os.getenv('INI_FILE_NAME')

# Variables for UT99 server management
SV = None
SV_ONLINE = False
CMD_PATH = '/../System/ucc.exe" '
CMD_COMMAND = 'server {map}?game={mode} ini={ini} log=server1.log'
BOT_PATH = os.path.dirname(os.path.realpath(__file__))

# List of supported modes
SV_MODES = {
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

# Map name prefixes for each mode
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

# Variables for bot initialization
INTENTS = discord.Intents.default()
INTENTS.message_content = True
BOT = commands.Bot(command_prefix="!", intents=INTENTS)

def get_maps (mode):
    """Returns the list of maps supported by the specified mode."""
    maps = glob.glob('{path}/../Maps/{mode}-*.unr'.format(path=BOT_PATH, mode=SV_MAPS[mode]))
    maps = [map_path.split('\\')[-1].split('.')[0] for map_path in maps]
    return maps

def get_random_map (mode):
    """Returns a random map for the specified mode."""
    maps = get_maps()
    rand_index = random.randrange(len(maps))
    return maps[rand_index]

def config_ini_file (mode, players):
    """Changes MinPlayer parameter in required .ini file for specified mode."""
    global INI_FILE, BOT_PATH
    config_file = INI_FILE
    if (mode in ("MonsterHunt", "MonsterArena", "MonsterDefence")):
        config_file = 'MonsterHunt.ini'
    for line in fileinput.input(BOT_PATH + '/../System/' + config_file, inplace=True):
        if line.strip().startswith('MinPlayers='):
            line = 'MinPlayers={min}\n'.format(min=players)
        sys.stdout.write(line)

async def get_map_choices (mode, current):
    """Returns the list of maps of a specific mode as Discord choices."""
    maps = get_maps(mode)
    maps = [discord.app_commands.Choice(name=map_name, value=map_name) for map_name in maps if (current in map_name.lower())]
    return maps[:25]

async def get_mode_choices(current):
    """Returns the available modes for the current version of the game as Discord choices."""
    modes = [
        discord.app_commands.Choice(name="DeathMatch", value="DeathMatch"),
        discord.app_commands.Choice(name="Team DeathMatch", value="TeamDeathMatch"),
        discord.app_commands.Choice(name="Capture the Flag", value="CaptureTheFlag"),
        discord.app_commands.Choice(name="Assault", value="Assault"),
        discord.app_commands.Choice(name="Domination", value="Domination"),
        discord.app_commands.Choice(name="Last Man Standing", value="LastManStanding")
    ]
    if (os.path.isfile(BOT_PATH + "/../System/MonsterHunt.u")):
        modes.extend([
            discord.app_commands.Choice(name="Monster Hunt", value="MonsterHunt"),
            discord.app_commands.Choice(name="Monster Arena", value="MonsterArena"),
            discord.app_commands.Choice(name="Monster Defence", value="MonsterDefence")
        ])
    if (os.path.isfile(BOT_PATH + "/../System/GunGame.u")):
        modes.append(discord.app_commands.Choice(name="Gun Game", value="GunGame"))
    return([mode for mode in modes if (current in mode.name.lower())])

# Function called when bot starts
@BOT.event
async def on_ready():
    try:
        synced = await BOT.tree.sync()
        print(f"Synced {len(synced)} commands(s).")
    except Exception as exception:
        print(exception)

# Argument descriptions for / commands
@app_commands.describe(
    mode="Choose the gamemode. Map will be selected randomly.",
    players="Bots will fill server if there are less than the desired amount of players.",
    map_name="Starting map of the server. Optional.")

# /run command decorators
@BOT.tree.command(name="run", description="Starts a UT99 server with the specified gamemode")
async def run(
        interaction: discord.Interaction,
        mode: str,
        players: int,
        map_name: str = "Random"):
    global SV, SV_ONLINE
    if (not SV_ONLINE):
        mode_class = SV_MODES[mode]
        map_file = get_random_map(mode) if map_name == "Random" else map_name
        config_ini_file(mode, players)
        command = '"' + BOT_PATH + CMD_PATH + CMD_COMMAND.format(map=map_file, mode=mode_class, ini=INI_FILE)
        try:
            SV = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=None,
                stderr=None,
                close_fds=True,
                encoding='utf8',
                creationflags=subprocess.CREATE_NEW_CONSOLE)
            SV_ONLINE = True
            await interaction.response.send_message("UT server online! Use **/join** for instructions on how to join")
            await BOT.change_presence(activity=discord.Game(name=mode))
        except:
            await interaction.response.send_message("Couldn't open server. Contact bot administrator.", ephemeral=True)
    else:
        await interaction.response.send_message("UT99 server already online!", ephemeral=True)

@run.autocomplete("mode")
async def autocomplete_mode(
    interaction: discord.Interaction,
    current: str):
    return await get_mode_choices(current.lower())

@run.autocomplete("map_name")
async def autocomplete_map(
    interaction: discord.Interaction,
    current: str):
    return await get_map_choices(interaction.namespace.mode, interaction.namespace.map_name.lower())


# /maps command decorators
@BOT.tree.command(name="maps", description="Shows a list of maps for given mode")
async def maps(interaction: discord.Interaction, mode: str):
    maps = get_maps(mode)
    message = ''
    for mapfile in maps:
        message += '* ' + mapfile + '\n'
    await interaction.response.send_message(message, ephemeral=True)

@maps.autocomplete("mode")
async def autocomplete_mode(
    interaction: discord.Interaction,
    current: str):
    return await get_mode_choices(current)

# /stop command decorators
@BOT.tree.command(name="stop", description="Forcefully stops the UT99 server")
async def stop(interaction: discord.Interaction):
    global SV_ONLINE
    if (not SV_ONLINE):
        await interaction.response.send_message("There isn't a UT99 server currently running", ephemeral=True)
    else:
        SV.kill()
        SV_ONLINE = False
        await interaction.response.send_message("UT99 server got monstruosly killed!")
        await BOT.change_presence(status=discord.Status.online, activity=None)

# /join command decorators
@BOT.tree.command(name="join", description="Gives instructions on how to join the UT99 server")
async def join(interaction: discord.Interaction):
    global SV_ONLINE
    if (not SV_ONLINE):
        await interaction.response.send_message("There isn't a UT99 server currently running", ephemeral=True)
    else:
        await interaction.response.send_message("Connect to **" + ip.get() + ":7777** through Multiplayer option 'Open Location'", ephemeral=True)

# /help command decorators
@BOT.tree.command(name="help", description="Give a list of the available commands")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message("* `/run [mode] [players] [map=Random]`:\n"+
                                            "   * Launches a server with the desired gamemode.\n"+
                                            " * The server will be filled with bots as to satisfy the amount of players specified as a minimum.\n"+
                                            " * Only one server can be launched by the bot at any time.\n"+
                                            " * The map is selected at random as a default, but can be optionally specified.\n"+
                                            "* `/maps [mode]`:\n"+
                                            "   * Shows the user a list of the available maps for a certain gamemode.\n"+
                                            "* `/stop`:\n"+
                                            "   * Forcefully stops the UT99 server\n"+
                                            "* `/join`:\n"+
                                            "   * Shows the user that sent the command an ephemeral message that indicates the current public IP and port of the running server, alongside instructions to join.\n"+
                                            "* `/help`:\n"+
                                            "   * Shows the user that sent the command an ephemeral message that explains each command supported by the bot.",
                                            ephemeral=True)

BOT.run(TOKEN)