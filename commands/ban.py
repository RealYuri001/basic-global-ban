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

__version__ = '1.1.0'

class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

        self.value = None
    
    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Done. Successfully confirmed.")
        self.value = True
        
        self.stop()
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Cancelling due to user request.")
        self.value = False
        
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
    
    @staticmethod
    async def gban_thingy(server, user, reason, succeded_in, errored_out_in):
        try:
            await server.ban(user, reason=reason)
            succeded_in.append(server.name)
        
        except discord.errors.Forbidden:
            errored_out_in[server.name] = "Permissions error!"
        
        except Exception as e:
            errored_out_in[server.name] = e
    
    @commands.command(aliases=['gb', 'gban', 'globalban'])
    @commands.is_owner()
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def global_ban(self, ctx, user: Union[commands.UserConverter, commands.MemberConverter], *, reason: str =None):

        if not user:
            self.global_ban.reset_cooldown(ctx)
            raise commands.errors.BadArgument
        
        if user == ctx.author:
            self.global_ban.reset_cooldown(ctx)
            return await ctx.send("You aren't allowed to ban yourself.")
        
        view = Confirm()
        await ctx.send("Do you wanna execute a global ban to {}?".format(str(user)), view=view)

        await view.wait()

        if not view.value:
            return
        
        elif view.value:
            await ctx.send("Successfully executed the ban to {}".format(str(user)))
            await asyncio.sleep(2)

            async with aiosqlite.connect("db/main.db") as db:
                async with db.cursor() as cursor:
                    await cursor.execute('SELECT * FROM banned_users')
                    
                    data = await cursor.fetchone()

                    if user.id in data and data:
                        self.global_ban.reset_cooldown(ctx)
                        return await ctx.send("This user is already banned.")
                    
                    else:
                        await cursor.execute("INSERT INTO banned_users VALUES (?, ?)", (user.id, reason if reason else "N/A"))
                        await db.commit()

                        await cursor.execute("SELECT * FROM banned_users")
                    
            errored_out_in = {}
            succeded_in = []
            
            reason = f"Global ban executed by {str(ctx.author)}. Reason: {reason}"
            
            tasks = (self.gban_thingy(server, user, reason, succeded_in, errored_out_in) for server in self.bot.guilds)
            
            await asyncio.gather(*tasks)
            
            succeded_in = ", ".join([f"`{server}`" for server in succeded_in])
            errored_out_in = "\n".join([f"**{t[0]}**: `{t[1]}`" for t in errored_out_in.values()])
            
            await ctx.send(f"I have banned the user from:\n{succeded_in}") if succeded_in else ...
            await ctx.send(f"I wasn't able to ban the user from these servers, the reasons are also given:\n{errored_out_in}") if errored_out_in else ...

        else:
            return
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
    
        async with aiosqlite.connect("db/main.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute('SELECT user_id FROM banned_users')
      
                data = await cursor.fetchall()
      
        if guild.members in data:
            try:
                for member in guild.members:
                    await member.ban(reason="Automatic ban-sync executed.")
        
            except discord.errors.Forbidden:
          
                for channel in guild.channels:
                    await channel.send("I can't ban these malicious users. Please move me higher than anyone else.")
                    break
      
        else:
            for ban_userid in data:
                try:
                    member = await self.bot.fetch_user(ban_userid[0])
                    await guild.ban(member, reason="Authorized auto ban sync.")
                
                except discord.errors.Forbidden:
                    pass

                except discord.errors.NotFound:
                    pass
    
    @commands.command()
    @commands.bot_has_permissions(ban_members=True)
    @commands.has_permissions(ban_members=True)
    async def executedlist(self, ctx):
        
        async with aiosqlite.connect("globalban.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute('SELECT * FROM banned_users')

                data = await cursor.fetchall()
                await ctx.trigger_typing()
                page = [
                    discord.Embed(
                        title="Global Banned ID",
                        description="List of all the banned user IDs.",
                        timestamp=discord.utils.utcnow(), 
                        color=0xe74c3c
                    )
                ]

                page_count = 0
                user_add_count = 0

                for user in data:
                    user_add_count += 1
                    
                    if user_add_count == 10:
                        page.append(discord.Embed(
                        title="Global Banned ID",
                        description="List of all the banned user IDs.",
                        timestamp=discord.utils.utcnow(), 
                        color=0xe74c3c
                    ))
                        page_count += 1
                        user_add_count = 0
                    
                    s = await self.bot.get_or_fetch_user(user[0])

                    page[page_count].add_field(name=f"{str(s)} - {s.id}", value=f"Reason: {user[1]}", inline=False)
                    page[page_count].set_footer(text="Malicious user lists are here.")

                pagination = pages.Paginator(
                    pages=page, 
                    author_check=True, 
                    timeout=30,
                    disable_on_timeout=True,
                )
                
                await pagination.send(ctx)
    
    @commands.command(aliases=["gunban"])
    @commands.bot_has_permissions(ban_members=True)
    @commands.cooldown(1, 300, commands.BucketType.guild)
    @commands.is_owner()
    async def global_unban(self, ctx, user: commands.UserConverter, reason: str=None):

        if not user:
            self.global_unban.reset_cooldown(ctx)
            raise commands.BadArgument
                
        view = Confirm()
        
        await ctx.send("Are you sure you wanna do that? (This will automatically unban in every servers bot are in.)", view=view)
        
        await view.wait()

        if not view.value:
            return
    
        elif view.value:
            for server in self.bot.guilds:
                try:
                    async for ban in server.bans(limit=None):
                        if ban.user == user:
                            await server.unban(user, reason=f"Automatic unbanned authorized by {ctx.author}. Reason: {reason}")
                    
                        else:
                            user = await self.bot.fetch_user(user.id)
                            await server.unban(user, reason=f"Automatic unbanned authorized by {ctx.author}. Reason: {reason}")
        
                except discord.errors.NotFound:
                    await ctx.send("This user is not found.")
                    pass
        
                except discord.errors.Forbidden:
                    pass

                async with aiosqlite.connect("db/main.db") as db:
                    async with db.cursor() as cursor:
                        await cursor.execute('SELECT user_id FROM banned_users WHERE user_id = ?', (user.id,))
          
                        data = await cursor.fetchone()

                        if data:
                            await cursor.execute('DELETE FROM banned_users WHERE user_id = ?', (user.id,))
                            await ctx.send('Sucessfully unbanned the user.')
                        
                    await db.commit()
          
        else:
            return
    
    @commands.Cog.listener()
    async def on_member_join(self, member):       
        
        async with aiosqlite.connect("db/main.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute('SELECT * FROM banned_users')
            
                data = await cursor.fetchall()
                banned_users = {}
                
                for x in data:
                  banned_users[x[0]] = x[1]
        
        if member.id in banned_users:
            try:
                reason = "Automatic joined ban-sync executed by an automatic system. Reason: {}".format(banned_users[member.id])
                await member.ban(reason=reason)
            
            except discord.errors.Forbidden:
                return

            except discord.errors.NotFound:
                return
        
        else:
            return
    
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        
        async with aiosqlite.connect("db/main.db") as db:
            async with db.cursor() as cursor:
                await cursor.execute('SELECT * FROM banned_users')

                data = await cursor.fetchall()
                unbanned_user = {}

                for y in data:
                    unbanned_user[y[0]] = y[1]
        
        async for entry in guild.audit_logs(action=discord.AuditLogAction.unban):
            if user.id == entry.target.id and user.id in unbanned_user:
                try:
                    reason = "Automatic unbanned ban-sync system executed."
                    await guild.ban(user, reason=reason)
                    await entry.user.send(f"Please do not ban {user}, they were global banned for this reason: {unbanned_user[user.id]}\nPlease consider joining a support server, so we could notify you if the member is unbanned!")
                    break
                
                except discord.errors.NotFound:
                    return
                
                except discord.errors.Forbidden:
                    return
                
                except discord.errors.HTTPException:
                    return
                
class View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

        self.value = None
    
    @discord.ui.button(emoji="🔨")
    async def do_ban(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Banning...")

        self.value = True

        self.stop()
  
    @discord.ui.button(emoji="❌")
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False

def setup(bot):
    bot.add_cog(SimpleGlobalBan(bot))
