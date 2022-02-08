import nextcord
from nextcord.ext import commands
import os
from keep_alive import keep_alive

intents = nextcord.Intents().all()

bot = commands.Bot(commands.when_mentioned_or(","), intents=intents, help_command=None)

@bot.event
async def on_ready():
    await bot.change_presence(status=nextcord.Status.idle)

for file in os.listdir('./commands'):
    if file.endswith('.py'):
        bot.load_extension("commands."+ file[:-3])

keep_alive()
bot.run('ODg0MTA0MjMzMjc0NzI4NDg5.YTToOw.XLdZOKmf9FGXC1r9KhSSsQ2a62E')