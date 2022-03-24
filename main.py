import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.all()

bot = commands.Bot(commands.when_mentioned_or(","), intents=intents, help_command=None, owner_ids=[]) #Put your own IDs here

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle)

for file in os.listdir('./commands'):
    if file.endswith('.py'):
        bot.load_extension("commands."+ file[:-3])

bot.run('token') #Put your own token here