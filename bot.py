"""
Discord bot implementation.
"""
import asyncio
from datetime import datetime, timedelta
import json
import os
import random
import discord
from discord.ext import commands
import logging
from sheets_client import SheetsClient
from config import config

logger = logging.getLogger(__name__)

class DiscordBot:
    """Discord bot class."""
    
    def __init__(self):
        # Set up bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        # Initialize bot with command prefix
        self.bot = commands.Bot(
            command_prefix=config.command_prefix,
            intents=intents,
            help_command=None  # Disable default help command
        )
        
        # Initialize Google Sheets client
        try:
            self.sheets_client = SheetsClient()
        except Exception as e:
            logger.error(f"Failed to initialize Sheets client: {e}")
            self.sheets_client = None
        
        # Set up event handlers and commands
        self._setup_events()
        self._setup_commands()
    
    def _setup_events(self):
        """Set up bot event handlers."""
        
        @self.bot.event
        async def on_ready():
            """Called when the bot is ready."""
            logger.info(f'{self.bot.user} has connected to Discord!')
            logger.info(f'Bot is in {len(self.bot.guilds)} guilds')
            if not os.path.exists(LOG_FILE):
                server = bot.get_guild(SERVER_ID)
                if not server:
                    return
                id = {}
                for member in server.members:
                    id[member.id] = {
                        'FIRST_UPDATE': datetime.now().strftime("%Y-%m-%d"),
                        'LAST_REACT' : datetime.now().strftime("%Y-%m-%d"),
                        'LAST_REMINDED': datetime.now().strftime("%Y-%m-%d")
                    }
                with open(LOG_FILE, "w", encoding="utf-8") as f:
                    json.dump(id, f, indent=4)
            
            bot.loop.create_task(reminder())
            
            # Set bot status
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{config.command_prefix}status | Google Sheets"
            )
            await self.bot.change_presence(activity=activity)
        
        @self.bot.event
        async def on_command_error(ctx, error):
            """Handle command errors."""
            if isinstance(error, commands.CommandNotFound):
                return  # Ignore unknown commands
            
            logger.error(f"Command error: {error}")
            
            # Send user-friendly error message
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while processing your command.",
                color=discord.Color.red()
            )
            
            if isinstance(error, commands.MissingRequiredArgument):
                embed.description = f"Missing required argument: {error.param}"
            elif isinstance(error, commands.BadArgument):
                embed.description = "Invalid argument provided."
            else:
                embed.description = "An unexpected error occurred. Please try again later."
            
            try:
                await ctx.send(embed=embed)
            except discord.HTTPException:
                # Fallback to plain text if embed fails
                await ctx.send(f"❌ Error: {embed.description}")
    
    def _setup_commands(self):
        """Set up bot commands."""
        
        @self.bot.command(name='status')
        async def status_command(ctx,*args):
            """
            Fetch and display status data from Google Sheets.
            
            Usage: c!status [worksheet_name]
            """
            if args:
                return
            worksheet = None
            # Send typing indicator
            async with ctx.typing():
                try:
                    # Check if sheets client is available
                    if not self.sheets_client:
                        embed = discord.Embed(
                            title="❌ Service Unavailable",
                            description="Google Sheets service is currently unavailable. Please contact an administrator.",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        return
                    
                    # Fetch data from Google Sheets
                    logger.info(f"Fetching status data for user {ctx.author} in guild {ctx.guild}")
                    data = self.sheets_client.get_status_data(worksheet)
                    
                    # Format the data
                    formatted_data: list = self.sheets_client.format_status_data(data)
                    #print(formatted_data)
                    # Send the response directly without embed for larger display
                    for line in formatted_data:
                        await ctx.send(line)
                    
                    logger.info(f"Successfully sent status data to {ctx.author}")
                
                except ValueError as e:
                    # Handle specific errors (e.g., worksheet not found)
                    embed = discord.Embed(
                        title="❌ Invalid Request",
                        description=str(e),
                        color=discord.Color.orange()
                    )
                    await ctx.send(embed=embed)
                
                except Exception as e:
                    logger.error(f"Error in status command: {e}")
                    
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Failed to fetch data from Google Sheets. Please try again later.",
                        color=discord.Color.red()
                    )
                    await ctx.send(embed=embed)
        
        @self.bot.command(name='help')
        async def help_command(ctx):
            """Display help information."""
            embed = discord.Embed(
                title="🤖 Bot Commands",
                description="Here are the available commands:",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name=f"{config.command_prefix}status",
                value="Thông báo trạng thái của các account đã được thêm vào. Các thông tin gồm: ID, Rank, Trạng thái, Map đang chơi. Account Valorant phải được kết bạn với ChaosMAX#9106 thì mới được cập nhật",
                inline=False
            )
            
            embed.add_field(
                name=f"{config.command_prefix}add {{id}}",
                value="Thêm id vào Sheet. Đảm bảo đã kết bạn với Valorant ChaosMAX#9106 để được cập nhật.",
                inline=False
            )
            
            embed.add_field(
                name=f"{config.command_prefix}help",
                value="Show this help message",
                inline=False
            )
            
            embed.set_footer(text="Bot powered by Google Sheets API")
            
            await ctx.send(embed=embed)
        
        @self.bot.command(name='add')
        async def add_command(ctx, *, user_id: str|None = None):
            """
            Add a new user ID to the Google Sheet.
            
            Usage: c!add {id}
            """
            if not user_id:
                await ctx.send("❌ Please provide a user ID. Usage: `c!add {id}`")
                return
            user_id = user_id.strip()
            
            # Send typing indicator
            async with ctx.typing():
                try:
                    # Check if sheets client is available
                    if not self.sheets_client:
                        await ctx.send("❌ Google Sheets service is currently unavailable.")
                        return
                    
                    # Add the new entry
                    logger.info(f"Adding new entry '{user_id}' requested by {ctx.author}")
                    success = self.sheets_client.add_new_entry(user_id)
                    
                    if success:
                        await ctx.send(f"✅ Đã thêm {user_id} vào. Kiểm tra xem đã kết bạn với acc Valorant ChaosMAX#9106 chưa.")
                        logger.info(f"Successfully added entry '{user_id}' for {ctx.author}")
                    else:
                        await ctx.send("❌ Failed to add entry to the sheet. Please try again.")
                        
                except Exception as e:
                    logger.error(f"Error in add command: {e}")
                    await ctx.send("❌ An error occurred while adding the entry.")

        @self.bot.command(name='ping')
        async def ping_command(ctx):
            """Check bot latency."""
            latency = round(self.bot.latency * 1000)
            
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Bot latency: {latency}ms",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            
        LOG_FILE = "log.json"
        SERVER_ID = 760008091827306498

        REMINDER_INTERVAL = 10 #days
        REMINDER_COOLDOWN = 120 # seconds. Prevent bot multi spam.
        REMINDER_COOLDOWN_USER = 4 #days
        REMINDER_CHANNEL = 1389554769634398299
        REMINDER_START_HOUR = 19
        REMINDER_END_HOUR = 21

        ID_OWNER = 1386556768737427466

        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.reactions = True
        intents.voice_states = True
        intents.members = True

        bot = commands.Bot(command_prefix="!", intents=intents)

        def log_event(event_type, user, details):
            id = user.id
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if id in data:
                event = data[id].get(event_type, [])
                if event:
                    if event['LAST_UPDATE'] != datetime.now().strftime("%Y-%m-%d"):
                        event['LAST_UPDATE'] = datetime.now().strftime("%Y-%m-%d")
                        event['COUNT'] += 1
                else:
                    data[id][event_type] = {
                        "LAST_UPDATE": datetime.now().strftime("%Y-%m-%d"),
                        "COUNT": 1
                    }
                data[id]['LAST_REACT'] = datetime.now().strftime("%Y-%m-%d")
            else:
                data[id] = {
                    'FIRST_UPDATE': datetime.now().strftime("%Y-%m-%d"),
                    event_type: {
                        "LAST_UPDATE": datetime.now().strftime("%Y-%m-%d"),
                        "COUNT": 1
                    }
                }
            
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                
        @self.bot.event
        async def on_message(message):
            if message.author.bot:
                return
            if message.guild.id != SERVER_ID:
                return
            
            log_event("MESSAGE", message.author, message.content)
            await bot.process_commands(message)

        @self.bot.event
        async def on_reaction_add(reaction, user):
            if user.bot:
                return
            if reaction.message.guild.id != SERVER_ID:
                return
            
            details = f"EMOJI: {reaction.emoji} | Message: {reaction.message.content}"
            log_event("REACTION_ADD", user, details)

        @self.bot.event
        async def on_voice_state_update(member, before, after):
            if member.bot:
                return
            if member.guild.id != SERVER_ID:
                return
            
            if before.channel != after.channel:
                if after.channel:
                    log_event("VOICE_JOIN", member, f"Joined: {after.channel.name}")

        async def reminder():
            await bot.wait_until_ready()
            channel = bot.get_channel(REMINDER_CHANNEL)
            if not channel:
                return
            if not isinstance(channel, discord.TextChannel):
                return
            
            while not bot.is_closed():
                today = datetime.now()
                
                #Check hour
                if today.hour < REMINDER_START_HOUR or today.hour >= REMINDER_END_HOUR:
                    await asyncio.sleep(REMINDER_COOLDOWN)
                    continue
                
                with open(LOG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                needRemind = []
                for id, data in data.items():
                    last_react = data.get('LAST_REACT', today.strftime("%Y-%m-%d"))
                    #Check how many days from last react
                    days_react = (today - datetime.strptime(last_react, "%Y-%m-%d")).days
                    if days_react < REMINDER_INTERVAL:
                        continue
                    
                    #Check how many days from last reminded
                    last_reminded = data.get('LAST_REMINDED', today.strftime("%Y-%m-%d"))
                    days = (today - datetime.strptime(last_reminded, "%Y-%m-%d")).days
                    if days < REMINDER_COOLDOWN_USER:
                        continue
                    
                    needRemind.append((id, days_react))
                
                if needRemind:
                    victim = random.choice(needRemind)
                    if random.randint(0, 1) == 0: #Spare with 50% chance
                        await channel.send(get_warning_message(victim[0], victim[1]))
                        data[victim[0]]['LAST_REMINDED'] = today.strftime("%Y-%m-%d")
                        with open(LOG_FILE, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4)
                    else:
                        #If not spare, write the LAST_REMINDED as the next day of old LAST_REMINDED
                        data[victim[0]]['LAST_REMINDED'] = (datetime.strptime(last_reminded, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                        with open(LOG_FILE, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4)
                
                await asyncio.sleep(REMINDER_COOLDOWN)
                    
        def get_warning_message(id, days_react):
            pingVictim = f"<@{id}>"
            pingOwner = f"<@&{ID_OWNER}>"
            
            if days_react <= 30:
                A = [
                    f"Uhm, {pingVictim}, được {days_react} rồi mà bro chưa về server rồi đấy",
                    f"{pingVictim}, thỉnh thoảng về server nói chuyện với ae đê",
                    f"{pingVictim}, ae chưa gặp nhau cỡ {days_react} rồi :>",
                    f"Kích hoạt ma pháp [Chaos Form], hiến tế {days_react} ngày để triệu hồi [{pingVictim}]"
                ]
                return random.choice(A)
            else: #ALERT
                A = [
                    f"Welp, {pingVictim}, hmmm, tôi chỉ muốn nói là bro có thể bị {pingOwner} ban vì không có hoạt động nào trong {days_react} ngày rồi",
                ]
                return random.choice(A)

        @self.bot.command()
        async def myinfo(ctx):
            user = ctx.author
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            userData = data.get(user.id, {})
            await ctx.send(f"""User: {user} 
        Số tin nhắn: {userData.get('MESSAGE_COUNT', 0)}
        Số lần vào voice: {userData.get('VOICE_COUNT', 0)}
        Số lần thả react: {userData.get('REACT_COUNT', 0)}
        Dữ liệu thu thập từ {userData.get('FIRST_UPDATE', "Không rõ")}
        """)
        
    
    async def start(self):
        """Start the Discord bot."""
        try:
            await self.bot.start(config.discord_token) # type: ignore
        except discord.LoginFailure:
            logger.error("Invalid Discord bot token")
            raise
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise
    
    async def close(self):
        """Close the Discord bot."""
        if not self.bot.is_closed():
            await self.bot.close()
            logger.info("Bot connection closed")
