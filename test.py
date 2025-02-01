import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import google.generativeai as genai

# 🔹 Telegram & Gemini Credentials
TOKEN = '7632070220:AAF1mft92tO1rlD4FCVWiFpVsmxWuBObZCk'
genai.configure(api_key="AIzaSyACJoyvGdD4XSe_DX4smQWzUQ9seMpc898")
model = genai.GenerativeModel("gemini-1.5-vision")

# 🔹 MongoDB Setup
uri = 'mongodb+srv://shaunmenezes1724:JGzEm8yOurwoiHHQ@cluster0.1o7tg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
mongo_client = MongoClient(uri, server_api=ServerApi('1'))
db = mongo_client['telegram_bot']
users_collection = db['users']
chats_collection = db['chats']
files_collection = db['files']

users_collection.create_index("user_id", unique=True)
chats_collection.create_index("user_id")

# 🔹 Start Command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    users_collection.update_one(
        {'user_id': user.id},
        {'$set': {'user_id': user.id, 'username': user.username, 'firstname': user.first_name}},
        upsert=True
    )
    await update.message.reply_text(f'Hello {user.first_name}! Send text or an image, and I will analyze it.')

# 🔹 Gemini AI Processing
async def process_text(update: Update):
    text = update.message.text
    user_id = update.message.from_user.id
    response = model.generate_content(text)

    # Store chat in MongoDB
    chat_data = {
        'user_id': user_id,
        'user_input': text,
        'bot_response': response.text,
        'timestamp': datetime.datetime.utcnow()
    }
    chats_collection.insert_one(chat_data)

    await update.message.reply_text(response.text)

async def process_image_or_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    timestamp = update.message.date

    # 🔹 Determine if it's a photo or file
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_name = f"user_{user_id}_image.jpg"
    elif update.message.document:
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name
        if not file_name.lower().endswith(('jpg', 'jpeg', 'png', 'pdf')):  # Restrict file types
            await update.message.reply_text("Only JPG, PNG, and PDF files are supported.")
            return
    else:
        await update.message.reply_text("Unsupported file type.")
        return

    # 🔹 Download File
    file = await context.bot.get_file(file_id)
    file_path = f"downloads/{file_name}"
    await file.download_to_drive(file_path)

    # 🔹 Save Metadata in MongoDB
    files_collection.insert_one({
        "user_id": user_id, "file_id": file_id, "file_path": file_path, "timestamp": timestamp
    })

    # 🔹 Send Image/File to Gemini
    try:
        with open(file_path, "rb") as image_file:
            response = model.generate_content([image_file])

        gemini_response = response.text if response else "Couldn't process the image."
    except Exception as e:
        gemini_response = f"Error processing image: {e}"

    await update.message.reply_text(f"Gemini says: {gemini_response}")

# 🔹 Setup Bot
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler('start', start_command))
app.add_handler(MessageHandler(filters.TEXT, process_text))
app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, process_image_or_file))

print("Bot is running...")
app.run_polling(poll_interval=3)
