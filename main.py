"""
Main entry point for the Discord bot application.
"""
import asyncio
import logging
from bot import DiscordBot
import keep_alive
keep_alive.keep_alive()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main function to run the Discord bot."""
    bot = DiscordBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        logging.info("Bot shutdown requested by user")
    except Exception as e:
        logging.error(f"Bot encountered an error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
