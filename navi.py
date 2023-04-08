import asyncio
import discord
import Color
import bot_token
from yt_dlp import YoutubeDL
from requests import get

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = discord.Client(intents=intents)

QUEUE = []

PREFIX = '>'
BOT_TOKEN = bot_token.BOT_TOKEN
FFMPEG_PATH = '/usr/bin/ffmpeg'
FFMPEG_BEFORE_OPTIONS = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'


@client.event
async def on_ready():
    print(Color.RED + f'We have logged in as {client.user}' + Color.ENDC)


@client.event
async def on_message(message):
    if message.author == client.user:   # Ignore message from bot
        return

    if message.content.startswith(PREFIX):
        # Gather message information for better readability
        message_data = message
        author = message.author
        message_content = message.content
        text_channel = message.channel
        if message.author.voice:
            voice_channel = message.author.voice.channel
        else:
            voice_channel = None
        # Determine if user is in channel with voice_client otherwise it is None
        voice_client = None
        for voice_client in client.voice_clients:
            if voice_client.channel == voice_channel:
                voice_client = voice_client
        # Split message content into command name and command arguments for processing
        message_content_list = message_content.split()
        command = message_content_list[0][1:]   # Trimming prefix as well
        command_args = ' '.join(message_content_list[1:])

        print_command_info(message_data)
        match command:
            case 'hello':
                await text_channel.send(f"**Hello, {author.display_name}**")
            case 'echo':
                await text_channel.send(f"**{command_args}**", tts=False)
            case 'join' | 'j' if voice_channel:   # Only attempt join if voice channel is not None (user is in a valid voice channel)
                await connect(voice_channel, message_data)
            case 'leave' | 'l' if voice_client:
                await disconnect(voice_client, voice_channel, message_data)
            case 'play' | 'p' if voice_channel and command_args:  # Only try if user in voice channel and command_args has data
                if voice_client is None:    # If bot is not connected
                    await connect(voice_channel, message_data)  # Try to connect
                    for voice_client in client.voice_clients:   # Fetch voice_client
                        if voice_client.channel == voice_channel:
                            voice_client = voice_client
                try:    # Try play
                    await play(voice_client, command_args, message_data)
                except:
                    pass
            case 'pause' if voice_client:
                voice_client.pause()
            case 'resume' if voice_client:
                voice_client.resume()
            case 'stop' if voice_client:
                QUEUE.clear()
                voice_client.stop()
            case 'skip' if voice_client:
                voice_client.stop()
            case 'queue' | 'q':
                if len(QUEUE) > 0:
                    await text_channel.send(f"```{format_queue()}```")
                else:
                    await text_channel.send('***Queue Empty***')
            case 'clear':
                QUEUE.clear()


def yt_search(arg):
    options = {'format': 'ba',  # Or bestaudio
               'noplaylist': 'true'}

    with YoutubeDL(options) as ydl:
        try:
            get(arg)
        except:
            video = ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]
        else:
            video = ydl.extract_info(arg, download=False)

    return video


def create_snippet(ydl_info):
    snippet = [[ydl_info['title'], ydl_info['original_url'], 'youtube']]
    return snippet


async def connect(voice_channel, message_data):
    try:
        await voice_channel.connect()
        print(Color.BLACK + f"{message_data.created_at}"[
                            :-13] + " " + Color.BLUE + "INFO     " + Color.PURPLE + "discord.voice_client " + Color.RED + f" Joining {voice_channel} in {message_data.guild}" + Color.ENDC)
    except Exception as e:
        print(Color.RED + 'Error connecting: ', e, Color.ENDC)


async def disconnect(voice_client, voice_channel, message_data):
    try:
        await voice_client.disconnect()
        print(Color.BLACK + f"{message_data.created_at}"[
                            :-13] + " " + Color.BLUE + "INFO     " + Color.PURPLE + "discord.voice_client " + Color.RED + f"Leaving {voice_channel} in {message_data.guild}" + Color.ENDC)
    except Exception as e:
        print(Color.RED + 'Error disconnecting: ', e, Color.ENDC)


def format_queue():
    formatted_queue = ''
    for each in QUEUE:
        formatted_queue += f"{each['title']} - {each['duration_string']}\n"
    return formatted_queue


async def send_now_playing_message(message_data, ytdlp_info):
    await message_data.channel.send(f"```Now Playing 👽 {ytdlp_info['title']} 👽 {ytdlp_info['duration_string']}```")


async def send_queueing_up_message(message_data, ytdlp_info):
    await message_data.channel.send(f"```Queueing Up 👽 {ytdlp_info['title']} 👽 {ytdlp_info['duration_string']}```")


async def play_next(voice_client, message_data):
    if len(QUEUE) > 0:
        await send_now_playing_message(message_data, QUEUE[0])
        current_song = QUEUE.pop(0)
        url = current_song['url']
        source = await discord.FFmpegOpusAudio.from_probe(url, before_options=FFMPEG_BEFORE_OPTIONS)

        def my_after(error):
            coro = play_next(voice_client, message_data)
            fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
            try:
                fut.result()
            except:
                pass    # an error happened running coro play_next

        voice_client.play(source, after=my_after)
    else:
        await message_data.channel.send('***Queue Empty, playback ending***')
        return


async def play(voice_client, command_args, message_data):
    ytdlp_info = yt_search(command_args)
    if voice_client.is_playing() or voice_client.is_paused():
        QUEUE.append(ytdlp_info)
        await send_queueing_up_message(message_data, ytdlp_info)
    else:
        await send_now_playing_message(message_data, ytdlp_info)
        url = ytdlp_info['url']
        source = await discord.FFmpegOpusAudio.from_probe(url, before_options=FFMPEG_BEFORE_OPTIONS)

        def my_after(error):
            coro = play_next(voice_client, message_data)
            fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
            try:
                fut.result()
            except:
                pass    # an error happened running coro play_next

        voice_client.play(source, after=my_after)


def print_command_info(message_data):
    print(Color.WHITE + '\u2500' * 36 + Color.ENDC)
    print(Color.CYAN + f"{message_data.created_at} UTC" + Color.ENDC)
    if message_data.author.voice:
        voice_channel = message_data.author.voice.channel
    else:
        voice_channel = None
    print(Color.BLUE + f"\tauthor: {message_data.author}\n\ttext_channel: {message_data.channel}\n\tvoice_channel: {voice_channel}" + Color.ENDC)
    # Split message content into command name and command arguments for processing
    message_content_list = message_data.content.split()
    command = message_content_list[0]
    command_args = ' '.join(message_content_list[1:])
    print(Color.PURPLE + command, Color.YELLOW + command_args + Color.ENDC)
    print(Color.WHITE + '\u2500' * 36 + Color.ENDC)


client.run(BOT_TOKEN)
