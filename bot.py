import os
import logging
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging (to see errors)
logging.basicConfig(level=logging.INFO)

# Get token & group id from Railway environment variables
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

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Daily standup bot activated ✅")

# /standup command (manual trigger)
async def standup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = generate_standup_text()
    members = ["@user1", "@user2", "@user3"]  # change to your Telegram usernames
    mentions = " ".join(members)
    await context.bot.send_message(GROUP_CHAT_ID, f"{mentions}\n{text}")

# Main app
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("standup", standup))

app.run_polling()
