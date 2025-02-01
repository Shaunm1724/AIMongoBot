import datetime
from typing import final
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import google.generativeai as genai

# Telegram Credentials
Token: final = '7632070220:AAF1mft92tO1rlD4FCVWiFpVsmxWuBObZCk'
BOT_USER_NAME: final = '@AiMongoBot'

# Gemini Credentials
genai.configure(api_key="AIzaSyACJoyvGdD4XSe_DX4smQWzUQ9seMpc898")
model = genai.GenerativeModel("gemini-1.5-flash")

# MONGO_URI = os.getenv("mongodb+srv://shaunmenezes1724:JGzEm8yOurwoiHHQ@cluster0.1o7tg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0", "mongodb://localhost:27017")

uri = 'mongodb+srv://shaunmenezes1724:JGzEm8yOurwoiHHQ@cluster0.1o7tg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
mongo_client = MongoClient(uri, server_api=ServerApi('1'))
db = mongo_client['telegram_bot']  # Database name
users_collection = db['users']  # Collection for user data
chats_collection = db['chats']  # Collection for user chats
files_collection = db['files']  # Collection for storing file metadata
users_collection.create_index("user_id", unique=True)
chats_collection.create_index("user_id")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #chatid firstname usdername  
    # await update.message.reply_text('Hello!!')
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    firstname = update.message.from_user.first_name
    chat_id = update.message.chat.id

    # Prepare user data
    user_data = {
        'user_id': user_id,
        'username': username,
        'firstname': firstname,
        'chat_id': chat_id
    }

    # Insert the user into MongoDB (if not already exists)
    users_collection.update_one(
        {'user_id': user_id},  # search by user_id
        {'$set': user_data},    # update data
        upsert=True             # if not found, insert new document
    )

    # await update.message.reply_text(f'Hello {firstname} (@{username})! Your data has been stored.')
    
    # Request phone number via a button
    contact_button = KeyboardButton('Send Phone Number', request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_button]], resize_keyboard=True)
    await update.message.reply_text('Please share your phone number with me:', reply_markup=reply_markup)



async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    phone_number = update.message.contact.phone_number
    username = update.message.from_user.username
    firstname = update.message.from_user.first_name

    # Prepare user data including phone number
    user_data = {
        'user_id': user_id,
        'username': username,
        'firstname': firstname,
        'phone_number': phone_number,
    }

    # Insert or update the user's data in MongoDB
    users_collection.update_one(
        {'user_id': user_id},  # search by user_id
        {'$set': user_data},    # update data
        upsert=True             # if not found, insert new document
    )

    # Send confirmation message
    await update.message.reply_text(f"Thank you, {firstname}! Your phone number has been saved: {phone_number}")



# async def user_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text('Hello!!')



# Not really needed

# async def gemini_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.message.from_user.id
#     text: str = update.message.text
#     response = model.generate_content(text)
#     timestamp = datetime.datetime.utcnow()

#     # Store the chat history (user input + bot response) in MongoDB
#     chat_data = {
#         'user_id': user_id,
#         'user_input': text,
#         'bot_response': response.text,
#         'timestamp': timestamp
#     }
    
#     # Insert chat history into the MongoDB 'chats' collection
#     chats_collection.insert_one(chat_data)


#     await update.message.reply_text(response.text)





async def image_file_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # user_id = update.message.from_user.id
    # file_id = update.message.document.file_id if update.message.document else update.message.photo[-1].file_id
    # file_name = update.message.document.file_name if update.message.document else 'image'

    #  # Retrieve file details
    # file = await context.bot.get_file(file_id)
    # file_path = file.file_path
    # file_extension = file_name.split('.')[-1].lower()

    # if file_extension not in ['jpg', 'jpeg', 'png', 'pdf']:
    #     await update.message.reply_text("Sorry, I can only process JPG, PNG, and PDF files.")
    #     return
    
    
    # await update.message.reply_text('Hello!!')

    
    user_id = update.message.from_user.id
    timestamp = update.message.date
    
    # Get highest-resolution image
    file_id = update.message.photo[-1].file_id

    # Download the file from Telegram
    file = await context.bot.get_file(file_id)
    file_path = f"downloads/user_{user_id}_image.jpg"
    await file.download_to_drive(file_path)

    # Store metadata in MongoDB
    file_data = {
        "user_id": user_id,
        "file_id": file_id,
        "file_path": file_path,
        "timestamp": timestamp
    }
    files_collection.insert_one(file_data)

    # Send image to Gemini AI
    try:
        with open(file_path, "rb") as image_file:
            response = model.generate_content([image_file])

        # Get response text
        gemini_response = response.text if response else "Couldn't process the image."
    except Exception as e:
        gemini_response = f"Error processing image: {e}"

    # Reply with Gemini's response
    await update.message.reply_text(f"Gemini says: {gemini_response}")




async def web_searching(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello!!')




async def handle_response(user_id, text: str) -> str:
    response = model.generate_content(text)
    timestamp = datetime.datetime.utcnow()

    # Store the chat history (user input + bot response) in MongoDB
    chat_data = {
        'user_id': user_id,
        'user_input': text,
        'bot_response': response.text,
        'timestamp': timestamp
    }
    
    # Insert chat history into the MongoDB 'chats' collection
    chats_collection.insert_one(chat_data)

    return response.text

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    user_id = update.message.from_user.id

    if message_type == 'group':
        if BOT_USER_NAME in text:
            new_text: str = text.replace(BOT_USER_NAME, '').strip()
            response: str = await handle_response(user_id, new_text)
        else:
            return
    else:
        response: str = await handle_response(user_id, text)

    await update.message.reply_text(response)


if __name__ == '__main__':
    print('Starting Bot..')
    app = Application.builder().token(Token).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('websearch', web_searching))
    app.add_handler(CommandHandler('imageorfile', image_file_analysis))

    # Handling the contact sharing
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Error
    app.add_error_handler(error)



    # Polling 
    print('Poling...')
    app.run_polling(poll_interval=3)









'''
in reality I just need the folowing commands

/start
/websearch

The rest is just noraml prompt with the gemini ai, both text and image or file
'''