"""
Discord bot implementation.
"""
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
