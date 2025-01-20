import discord
import os
from dotenv import load_dotenv
import yt_dlp as youtube_dl
from discord.ext import commands
from discord import app_commands
import asyncio

FFMPEG_PATH = r'F:\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe'


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# intents
intents = discord.Intents.default()
intents.message_content = True

# init bot with intents
bot = commands.Bot(command_prefix='g!', intents=intents)

# downloader options etc
ydl_opts = {
    'format': 'bestaudio',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
    }],
}

@bot.tree.command(name="ping", description="Responds with Pong!")
async def ping(interaction: discord.Interaction):
    try:
        await interaction.response.send_message("Pong!")
    except discord.errors.NotFound:
        print("Interaction expired before responding.")

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="g!help for commands"))
    print('Bot is now online and ready!')
    
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    if not member.bot:  # ignore all self bot state changes
        voice_client = member.guild.voice_client
        if voice_client and len([m for m in voice_client.channel.members if not m.bot]) == 0:
            await asyncio.sleep(300)  # wait 5 min
            # check again after waiting to see if its still empty
            if voice_client and len([m for m in voice_client.channel.members if not m.bot]) == 0:
                await voice_client.disconnect()


@bot.command()
async def play(ctx, *, query):
    if not ctx.author.voice:
        await ctx.send("You are not connected to a voice channel.")
        return

    channel = ctx.author.voice.channel

    if ctx.voice_client is None:
        await channel.connect()
    elif ctx.voice_client.channel != channel:
        await ctx.voice_client.move_to(channel)

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        url = info['url']  # no formatting [FORMATS]
        
        ctx.voice_client.stop()
        
        FFMPEG_OPTIONS = {
            'options': '-vn',
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        }
        
        ctx.voice_client.play(discord.FFmpegOpusAudio(url, executable=FFMPEG_PATH, **FFMPEG_OPTIONS))
        await ctx.send(f"Now playing: {info['title']}")
    except Exception as e:
        await ctx.send(f"An error occurred while searching for the song: {str(e)}")
        print(f"Error details: {e}")
        import traceback
        traceback.print_exc()
        
@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        await ctx.send("Stopped playing audio.")
    else:
        await ctx.send("I'm not playing any audio.")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Left the voice channel.")
    else:
        await ctx.send("I'm not in a voice channel.")

@bot.command()
async def join(ctx):
    if not ctx.author.voice:
        await ctx.send("You are not connected to a voice channel.")
        return
        
    channel = ctx.author.voice.channel
    
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
        await ctx.send(f"Moved to {channel.name}")
    else:
        await channel.connect()
        await ctx.send(f"Joined {channel.name}")


bot.run(TOKEN)
