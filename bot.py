import os
import logging
from datetime import datetime
import pytz
import asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Environment variables
TOKEN = os.getenv("TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID"))

# In-memory store of users (key = user_id, value = username/first_name)
group_members = {}

# Format today date
def get_today():
    tz = pytz.timezone("Asia/Jakarta")
    return datetime.now(tz).strftime("%d %b %Y")

# Function to fetch members and send standup questions
async def send_standup(bot):
    try:
        if not group_members:
            mentions = "everyone"
        else:
            mentions = " ".join(group_members.values())

        message = (
            f"📅 {get_today()}\n\n"
            f"{mentions}\n\n"
            "- What did you do today?\n"
            "- Do you have any blocker?\n"
            "- What is your plan for tomorrow?"
        )

        await bot.send_message(chat_id=GROUP_CHAT_ID, text=message)
        logging.info("✅ Standup message sent")
    except Exception as e:
        logging.error(f"❌ Error sending standup: {e}")

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Daily standup bot activated!")

async def manual_standup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_standup(context.bot)

# Message handler to track users
async def track_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_CHAT_ID:
        return  # only track in target group

    user = update.effective_user
    if not user:
        return

    if user.username:
        name = f"@{user.username}"
    else:
        name = user.first_name

    group_members[user.id] = name
    logging.info(f"👤 Tracked member: {name}")

# Scheduler hook
async def post_init(app: Application):
    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Jakarta"))
    scheduler.add_job(
        lambda: app.create_task(send_standup(app.bot)),
        trigger="cron",
        day_of_week="mon-fri",   # ✅ only weekdays
        hour=17,
        minute=50
    )
    scheduler.start()
    logging.info("📅 Scheduler started (Mon–Fri, 17:00 Asia/Jakarta)")

# Main
def main():
    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("standup", manual_standup))

    # Track all messages to build member list
    application.add_handler(MessageHandler(filters.ALL, track_members))

    application.run_polling()

if __name__ == "__main__":
    main()
