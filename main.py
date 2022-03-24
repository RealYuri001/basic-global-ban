#!python3
#-*- coding: utf-8 -*-

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from keep_alive import keep_alive

load_dotenv()

intents = discord.Intents.all()

bot = commands.Bot(commands.when_mentioned_or(","), intents=intents, help_command=None, owner_ids=[]) #Put your own IDs here

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle)
    print("I am ready!")

for file in os.listdir('./commands'):
    if file.endswith('.py'):
        bot.load_extension("commands."+ file[:-3])

keep_alive()
bot.run('token') #Put your own token here
