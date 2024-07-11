# Server Manager: Unreal Tournament 99
## Description
A Discord bot written in Python for launching and managing an Unreal Tournament 99 server.  
Commands are explained in the **Commands** section, and can be seen with a brief explanation during runtime by typing /help in the chat of the server it is in.

## Setup
Clone this repository in the root folder of your installation of Unreal Tournament.

Create a .env file with the next lines, replacing the values in brackets:

    DISCORD_TOKEN=[Token from Discord server]
    DISCORD_GUILD=[Name of Discord server]
    INI_FILE_NAME=[.ini file for UT99 server]

## Run
To start the bot execute the command:

    python bot.py

## Commands
* **/run [gamemode] [players]**: This command launches a server with the desired gamemode. The server will be filled with bots as to satisfy the amount of players specified as a minimum. Only one server can be launched by the bot at any time.

* **/maps**: Shows the user a list of the available maps for a certain gamemode.

* **/stop**: Stops the currently running server.

* **/join**: Shows the user that sent the command an ephemeral message that indicates the current public IP and port of the running server, alongside instructions to join.

* **/help**: Shows the user that sent the command an ephemeral message that explains each command supported by the bot.

## Notes
* The bot checks if certain files are present to see what gamemodes and maps are available.

* The configurations of the server are defined by the .ini file given to it, and to determine which file to use its name can be pointed out in the INI_FILE_NAME field in the .env file. By default it uses UnrealTournament.ini which is the file used by the game when playing.