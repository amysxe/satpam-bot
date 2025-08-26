import os
import logging
import datetime
import pytz
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

# Generate daily standup text
def generate_standup_text():
    today = datetime.datetime.now().strftime("%d %b %Y")
    return f"""{today}
- What did you do today?
- Do you have any blocker?
- What is your plan for tomorrow?
"""

# Fetch all visible members (requires bot to be Admin)
async def get_group_usernames(context: ContextTypes.DEFAULT_TYPE):
    try:
        members = await context.bot.get_chat_administrators(GROUP_CHAT_ID)
        usernames = []
        for m in members:
            if m.user.username:
                usernames.append("@" + m.user.username)
            else:
                usernames.append(m.user.first_name)  # fallback
        return " ".join(usernames) if usernames else "Team"
    except Exception as e:
        logging.error(f"Error fetching members: {e}")
        return "Team"

# Send standup message
async def send_standup(context: ContextTypes.DEFAULT_TYPE):
    mentions = await get_group_usernames(context)
    text = generate_standup_text()
    await context.bot.send_message(GROUP_CHAT_ID, f"{mentions}\n{text}")

# Manual command
async def standup(update, context: ContextTypes.DEFAULT_TYPE):
    await send_standup(context)

def main():
    app = Application.builder().token(TOKEN).build()

    # Manual command
    app.add_handler(CommandHandler("standup", standup))

    # Scheduler: 5PM Asia/Jakarta
    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Jakarta"))
    scheduler.add_job(
        lambda: app.job_queue.application.create_task(send_standup(app)),
        trigger="cron",
        hour=17,
        minute=0
    )
    scheduler.start()

    print("BOT IS RUNNING ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
