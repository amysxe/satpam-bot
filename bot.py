import logging
import os
import pytz
from datetime import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIG ---
BOT_TOKEN = os.getenv("TOKEN")  # set in Railway variables
GROUP_ID = os.getenv("GROUP_CHAT_ID")  # your group chat ID (string)
JAKARTA_TZ = pytz.timezone("Asia/Jakarta")

# ==============================
# STANDUP QUESTIONS
# ==============================
STANDUP_QUESTIONS = (
    "👋 Standup time!\n\n"
    "1. What did you work on yesterday?\n"
    "2. What are you working on today?\n"
    "3. Any blockers?"
)

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
    """Job that sends standup to the group"""
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
        # normalize input (accepts 9:5, 09:05, 18:9, etc.)
        parts = context.args[0].split(":")
        if len(parts) != 2:
            raise ValueError("Invalid format")

        hour = int(parts[0])
        minute = int(parts[1])

        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError("Invalid range")

        job_time = time(hour=hour, minute=minute, tzinfo=JAKARTA_TZ)

        chat_id = update.effective_chat.id

        # Remove old job if exists
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        for job in current_jobs:
            job.schedule_removal()

        # Add new job (Mon–Fri only)
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
        await update.message.reply_text(
            "❌ Invalid time format. Try: /settime 09:00 or /settime 18:30"
        )

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
