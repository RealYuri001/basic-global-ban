"""
The MIT License (MIT)

Copyright (c) 2022-present RealKiller666

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from typing import Union
import asyncio

import discord
from discord.ext import commands
import aiosqlite

class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

        self.value = None
        self.disabled = False
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Done. Successfully confirmed.")
        self.value = True
        self.disabled = True
        self.stop()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Cancelling due to user request.")
        self.value = False
        self.disabled = True
        self.stop()
    
class SimpleGlobalBan(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        async with aiosqlite.connect("db/main.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute('CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER NOT NULL, reason TEXT)')
            
            await db.commit()
    
    @commands.command(aliases=['gb', 'gban', 'globalban'])
    @commands.is_owner()
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def global_ban(self, ctx, user: Union[commands.UserConverter, commands.MemberConverter], *, reason: str =None):

        if not user:
            raise commands.errors.BadArgument
        
        view = Confirm()
        await ctx.send("Do you wanna execute a global ban to {}?".format(str(user)), view=view)

        await view.wait()

        if not view.value:
            return
        
        elif view.value:
            await ctx.send("Successfully executed the ban to {}".format(str(user)))
            await asyncio.sleep(2)
            
            for server in self.bot.guilds:
                if user in server:
                    try:
                        user = server.get_member(user.id)
                        await server.ban(user, reason=f"Global ban executed by {str(ctx.author)}. Reason: {reason}")
                    
                    except discord.errors.Forbidden:
                        return await ctx.send("I need a ban permission to ban that user or move me to higher than that users.")
                    
                    except discord.errors.NotFound:
                        return await ctx.send("User you're provided is not found. Make sure to double-check before banning.")
                else:
                    user = server.fetch_user(user.id)
                    await server.ban(user, reason=f"Global ban executed by {ctx.author}. Reason: {reason}")
        
        else:
            return
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        
        async with aiosqlite.connect("globalban.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute('SELECT user_id FROM banned_users')
      
            data = await cursor.fetchall()
      
        if guild.members in data:
            try:
                for members in data:
                    await members.ban(members, reason="Automatic ban-sync executed.")
        
            except discord.errors.Forbidden:
          
                for channel in guild.channels:
                    await channel.send("I can't ban these malicious users. Please move me higher than anyone else.")
                    break
            
            except discord.errors.NotFound:
                pass

        else:
            return

    @commands.command()
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def executedlist(self, ctx):
        
        async with aiosqlite.connect("globalban.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute('SELECT * FROM banned_users')

                data = await cursor.fetchall()
                await ctx.trigger_typing()
                embed = discord.Embed(title="Global banned ID", timestamp=discord.utils.utcnow(), color=0xe74c3c)
        
                msg = ""
                for ban_userid in data:
                    mention_user = f"<@!{ban_userid[0]}>"
                    msg += f"{mention_user} - `{ban_userid[0]}`. Reason: {ban_userid[1]}\n"

                embed.add_field(name="ID list & Reason", value=f"{msg}" if data else "**None**")
        
                embed.set_footer(text="All of malicious users are here!")
                view = View()
                f = await ctx.send(embed=embed, view=view)

                await view.wait()
                if view.value is None:
                    return
        
                elif view.value:
                    for server in self.bot.guilds:
                        if ban_userid[0] in server.members:
                            continue

                        try:
                            member = server.get_member(ban_userid[0])
                            
                            await ctx.trigger_typing()
                            await server.ban(member, reason=f"Mass malicious users list banned. Authorized by {str(ctx.author)}")
                            
                            await asyncio.sleep(0.25)

                        except discord.NotFound:
                            await ctx.send("This user is not found.")
                            pass
        
                        except discord.Forbidden:
                            await ctx.send("I don't have a permission to do that.")
                            pass
              
                        except Exception as e:
                            print(e)
            
                    else:
                        await ctx.trigger_typing()
                        member = await self.bot.get_or_fetch_user(ban_userid[0])
                        try:
                            if member in await server.bans():
                                pass
                        
                            await server.ban(member, reason=f"Mass malicious users list banned. Authorized by {str(ctx.author)}")
              
                        except discord.NotFound:
                            await ctx.send("This user is not found.")
                            pass
                    
                        except discord.Forbidden:
                            await ctx.send("I'm missing permissions to mass ban a user.")
                            return

                else:
                    await f.delete()
    
    @commands.command(aliases=["gunban"])
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 300, commands.BucketType.guild)
    @commands.is_owner()
    async def global_unban(self, ctx, user: commands.UserConverter, reason: str=None):
        
        view = Confirm()
        
        await ctx.send("Are you sure you wanna do that? (This will automatically unban in every servers bot are in.)", view=view)
        
        await view.wait()

        if not view.value:
            return
    
        elif view.value:
            for server in self.bot.guilds:
                try:
                    if user in await server.bans():
                        await server.unban(user, reason=f"Automatic unbanned authorized by {ctx.author}. Reason: {reason}")
                    
                    else:
                        user = await self.bot.fetch_user(user.id)
                        await server.unban(user, reason=f"Automatic unbanned authorized by {ctx.author}. Reason: {reason}")
        
                except discord.NotFound:
                    await ctx.send("This user is not found.")
                    pass
        
                except discord.Forbidden:
                    return await ctx.send("I don't a permission to do that")    

                async with aiosqlite.connect("globalban.db") as db:
                    async with db.cursor() as cursor:
                        await cursor.execute('SELECT user_id FROM banned_users')
          
                        data = await cursor.fetchone()

                        if data:
                            await cursor.execute('DELETE user_id FROM banned_users WHERE user_id = ?', (user.id))
                            await db.commit()
                            await ctx.send('Sucessfully unbanned the user.')
          
        else:
            return
        
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
    
        async with aiosqlite.connect("globalban.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute('SELECT user_id FROM banned_users')
      
                data = await cursor.fetchall()
      
        if guild.members in data:
            try:
                for member in guild.members:
                    await member.ban(reason="Automatic ban-sync executed.")
        
            except discord.Forbidden:
          
                for channel in guild.channels:
                    await channel.send("I can't ban these malicious users. Please move me higher than anyone else.")
                    break
      
        else:
            for ban_userid in data:
                try:
                    member = await self.bot.fetch_user(ban_userid[0])
                    await guild.ban(member, reason="Authorized automatic ban sync.")
                
                except discord.Forbidden:
                    pass

                except discord.NotFound:
                    pass
    
class View(discord.ui.View):
    def __init__(self):
        super().__init__()

        self.value = None
    
    @discord.ui.button(emoji="🔨")
    async def do_ban(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Banning...")
        
        self.value = True
        self.stop()
  
    @discord.ui.button(emoji="❌")
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()

def setup(bot):
    bot.add_cog(SimpleGlobalBan(bot))