import logging
import sqlite3
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Введите ваш токен сюда
TELEGRAM_TOKEN = '6172133477:AAHbySYc2ealCwulrSjNXfHcN6kvsRjXzvE'


def create_database():
    connection = sqlite3.connect('questions.db')
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            username TEXT,
            question TEXT,
            is_answered INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            username TEXT,
            message TEXT,
            direction TEXT
        )
    ''')

    connection.commit()
    connection.close()



def start(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(f"Hello, {user.first_name}! Ask your question.")


def handle_message(update: Update, context: CallbackContext):
    user = update.effective_user
    chat_id = update.message.chat_id
    question = update.message.text

    connection = sqlite3.connect('questions.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO messages (chat_id, username, message, direction) VALUES (?, ?, ?, ?)',
                   (chat_id, user.username, question, 'incoming'))
    connection.commit()

    cursor.execute('INSERT INTO questions (chat_id, username, question, is_answered) VALUES (?, ?, ?, ?)',
                   (chat_id, user.username, question, 0))
    connection.commit()
    connection.close()

    update.message.reply_text(f"Thank you, {user.first_name}! Your question has been received. We will respond as quickly as we can.")

def show_dialog(update: Update, context: CallbackContext):
    if len(context.args) < 1:
        update.message.reply_text("Please enter username.")
        return

    username = context.args[0]

    connection = sqlite3.connect('questions.db')
    cursor = connection.cursor()
    cursor.execute('SELECT message, direction FROM messages WHERE username = ? ORDER BY id', (username,))
    messages = cursor.fetchall()
    connection.close()

    if messages:
        dialog = ""
        for message, direction in messages:
            dialog += f"{direction.capitalize()}: {message}\n"
        update.message.reply_text(dialog)
    else:
        update.message.reply_text(f"There are no messages from user {username}.")


def view_unanswered_questions(update: Update, context: CallbackContext):
    connection = sqlite3.connect('questions.db')
    cursor = connection.cursor()
    cursor.execute('SELECT id, username, question FROM questions WHERE is_answered = 0')
    questions = cursor.fetchall()
    connection.close()

    if questions:
        for question in questions:
            update.message.reply_text(f"ID: {question[0]}, Username: {question[1]}, Question: {question[2]}")
    else:
        update.message.reply_text("No unread question.")


def answer_question(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("Please enter question ID and answer text.")
        return

    question_id = int(context.args[0])
    answer_text = ' '.join(context.args[1:])

    connection = sqlite3.connect('questions.db')
    cursor = connection.cursor()
    cursor.execute('SELECT chat_id, username FROM questions WHERE id = ?', (question_id,))
    result = cursor.fetchone()

    if result:
        chat_id, username = result
        context.bot.send_message(chat_id=chat_id, text=f"{answer_text}")
        cursor.execute('INSERT INTO messages (chat_id, username, message, direction) VALUES (?, ?, ?, ?)',
                       (chat_id, username, answer_text, 'outgoing'))
        connection.commit()

        cursor.execute('UPDATE questions SET is_answered = 1 WHERE id = ?', (question_id,))
        connection.commit()
        connection.close()
    else:
        update.message.reply_text("Question with this ID was not found.")



def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CommandHandler('secret', view_unanswered_questions))
    dp.add_handler(CommandHandler('answer', answer_question, pass_args=True))
    dp.add_handler(CommandHandler('showdialog', show_dialog, pass_args=True))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    create_database()
    main()
