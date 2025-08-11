"""
Main entry point for the Discord bot application.
"""
import asyncio
import logging
from bot import DiscordBot
import keep_alive
keep_alive.keep_alive()

class HTMLFilter(logging.Filter):
    def filter(self, record):
        msg = str(record.getMessage())
        if "<html" in msg.lower():
            # Lưu HTML vào file
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"cloudflare_error_{timestamp}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(msg)
            
            # Ghi log ngắn gọn
            short_msg = f"[Discord Error] Nhận HTML từ server — đã lưu vào {filename}"
            record.msg = short_msg
            record.args = ()
        return True

# Thêm filter vào logger của discord
discord_logger = logging.getLogger("discord")
discord_logger.addFilter(HTMLFilter())

# Cấu hình logging nếu chưa có
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
