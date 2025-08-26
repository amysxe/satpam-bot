import logging
import os
import pytz
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")  # set in Railway variables
GROUP_ID = os.getenv("GROUP_ID")    # your group chat ID
TIMEZONE = pytz.timezone("Asia/Jakarta")

# Scheduler
scheduler = AsyncIOScheduler(timezone=TIMEZONE)
job_id = "standup_job"

# --- BOT FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I’ll help with daily standups.\n"
        "Commands:\n"
        "• /standup → send questions now\n"
        "• /settime HH:MM → set daily standup time (WIB)"
    )

async def standup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_standup(context.bot)

async def send_standup(bot):
    today = datetime.now(TIMEZONE).strftime("%d %b %Y")
    logging.info("⏰ Triggered standup job")

    text = (
        f"📅 *{today}* — Daily Standup\n\n"
        "- What do you today?\n"
        "- Do you have any blocker?\n"
        "- What is your plan for tomorrow?"
    )

    await bot.send_message(
        chat_id=GROUP_ID,
        text=text,
        parse_mode="Markdown"
    )

async def settime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global job_id
    if not context.args:
        await update.message.reply_text("⏰ Usage: /settime HH:MM (24h, WIB)")
        return

    try:
        hour, minute = map(int, context.args[0].split(":"))
    except ValueError:
        await update.message.reply_text("⚠️ Invalid format. Use HH:MM")
        return

    # Remove old job
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    # Add new job
    scheduler.add_job(
        lambda: context.application.create_task(send_standup(context.bot)),
        trigger="cron",
        day_of_week="mon-fri",
        hour=hour,
        minute=minute,
        id=job_id
    )

    await update.message.reply_text(f"✅ Standup time set to {hour:02d}:{minute:02d} WIB (Mon–Fri)")

# --- MAIN APP ---
def main():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("standup", standup))
    application.add_handler(CommandHandler("settime", settime))

    application.run_polling()

async def post_init(app: Application):
    # Start scheduler
    if not scheduler.running:
        scheduler.start()
    # Default 17:00 Mon–Fri
    if not scheduler.get_job(job_id):
        scheduler.add_job(
            lambda: app.create_task(send_standup(app.bot)),
            trigger="cron",
            day_of_week="mon-fri",
            hour=17,
            minute=0,
            id=job_id
        )
    logging.info("📅 Scheduler initialized (Mon–Fri 17:00 WIB)")

if __name__ == "__main__":
    main()
