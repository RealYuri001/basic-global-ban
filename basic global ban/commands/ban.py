import nextcord
from nextcord.ext import commands
import sqlite3
import datetime

class ConfirmReport(nextcord.ui.View):
  def __init__(self):
      super().__init__()
      self.value = None

  @nextcord.ui.button(label="Confirm", style= nextcord.ButtonStyle.green)
  async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
    await interaction.response.send_message("Done.", ephemeral=True)
    self.value = True
    self.stop()
  
  @nextcord.ui.button(label="Cancel", style= nextcord.ButtonStyle.red)
  async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
    await interaction.response.send_message("Done. Cancelling...", ephemeral=True)
    self.value = False
    self.stop()

class GlobalBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('main.db')
        self.c = self.conn.cursor()
        self.c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER guild INTEGER)")
    
    @commands.command()
    @commands.is_owner()
    async def global_ban(self, ctx, member: commands.MemberConverter,*, reason):
     view = ConfirmReport()
     await ctx.send("Are you sure you want to send a global ban?", view=view)
     await view.wait()
     if view.value is None:
        return
     elif view.value:
        await ctx.send(f"Banned {member.name}. Updating database for global ban...")
        await ctx.send("Updated. They will get global ban in every servers if they have our bot.")
        for server in self.bot.guilds:
            if member in server.members:
                try:
                    member = server.fetch_member(member.id)
                    await member.ban(reason=f"Global ban executed by {ctx.author}. Reason: {reason}")
                except Exception as e:
                    print(e)
                self.c.execute('SELECT id FROM users WHERE guild = ?', (ctx.guild.id,))
                data = self.c.fetchone()
                if data:
                    self.c.execute('UPDATE users SET id = ? WHERE guild = ?', (member.id, ctx.guild.id,))
                else:
                    self.c.execute('INSERT INTO users (id, guild) VALUES (?, ?)', (member.id, ctx.guild.id,))
                
            self.conn.commit()
     else:
         await ctx.send("Affirmative.")

    @commands.command()
    async def executedlist(self, ctx):
        self.c.execute('SELECT * FROM users')
        data = self.c.fetchall()
        for ban in data:
            embed = nextcord.Embed(title="IDs of members who got global ban executed.")
            embed.add_field(name="ID list", value=f"<@{ban[0]}> {ban[0]}. Reason: {get_reason}")
            embed.set_footer(text="Basic global ban system made by Mr.Nab#0730")
            await ctx.send(embed=embed)
    
    async def get_reason(self, guild: nextcord.Guild, action: nextcord.AuditLogAction, target) -> str:
        await asyncio.sleep(5)

        before_sleep = datetime.datetime.utcnow() - datetime.timedelta(seconds=15)
        async for entry in guild.audit_logs(limit=25, after=before_sleep, action=action):
            if entry.target != target:
                continue

            return entry.reason if entry.reason is not None else 'no reason specified'
        return 'no reason found'

def setup(bot):
    bot.add_cog(GlobalBan(bot))
