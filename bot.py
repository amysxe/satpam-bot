import logging
import os
import pytz
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIG ---
BOT_TOKEN = os.getenv("TOKEN")  # set in Railway variables
GROUP_ID = os.getenv("GROUP_CHAT_ID")    # your group chat ID
TIMEZONE = pytz.timezone("Asia/Jakarta")

# ==============================
# LOGGING
# ==============================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ==============================
# COMMAND HANDLERS
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! 👋\n\n"
        "Use /standup to start manually.\n"
        "Use /settime HH:MM to schedule daily standups (Asia/Jakarta timezone)."
    )

async def standup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(STANDUP_QUESTIONS)

async def standup_job(context: ContextTypes.DEFAULT_TYPE):
    """Job that sends standup only on weekdays"""
    weekday = pytz.utc.localize(context.job.when).astimezone(JAKARTA_TZ).weekday()
    if weekday < 5:  # Monday=0 ... Friday=4
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text=STANDUP_QUESTIONS
        )

async def settime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Schedule standup at a specific time (Jakarta)"""
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /settime HH:MM (24h format)")
        return

    try:
        hour, minute = map(int, context.args[0].split(":"))
        job_time = time(hour=hour, minute=minute, tzinfo=JAKARTA_TZ)

        chat_id = update.effective_chat.id

        # Remove old job if exists
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        for job in current_jobs:
            job.schedule_removal()

        # Add new job
        context.job_queue.run_daily(
            standup_job,
            time=job_time,
            days=(0, 1, 2, 3, 4),  # Monday–Friday
            chat_id=chat_id,
            name=str(chat_id),
        )

        await update.message.reply_text(
            f"✅ Daily standup scheduled at {hour:02}:{minute:02} (Asia/Jakarta, Mon–Fri)"
        )
    except Exception as e:
        logging.error("Error in /settime: %s", e)
        await update.message.reply_text("❌ Invalid time format. Use HH:MM (e.g. /settime 17:30)")

# ==============================
# MAIN
# ==============================
def main():
    if not BOT_TOKEN:
        raise ValueError("❌ BOT TOKEN not set. Add it as 'TOKEN' in Railway variables.")

    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("standup", standup))
    application.add_handler(CommandHandler("settime", settime))

    # Run bot
    application.run_polling()

if __name__ == "__main__":
    main()
