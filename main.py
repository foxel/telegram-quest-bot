import atexit
import json
import random
import time
from typing import Dict, List, Union

import telebot
import yaml
from telebot.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

RESET_MESSAGE = 'Начать заново'

# load config from config.yml
with open('config.yml') as config_file:
    config = yaml.safe_load(config_file)

questions: List[Dict] = config['questions']

bot = telebot.TeleBot(config['token'], parse_mode='Markdown')
progress: Dict[int, int] = {}


def save_state():
    with open('state.json', 'w') as state_file:
        json.dump(progress, state_file)


def load_state():
    try:
        with open('state.json') as state_file:
            for user_id, question_id in dict(json.load(state_file)).items():
                progress[int(user_id)] = int(question_id)
    except FileNotFoundError:
        pass


# on exit save state
atexit.register(save_state)
load_state()
random.seed()


def markup(message: Union[str, List[str]]) -> str:
    # if message is a list, choose random element
    if isinstance(message, list):
        message = random.choice(message)

    return message.replace('\n', '\n\n')


def send_question(user_id: int):
    question_id = progress[user_id]
    keyboard = ReplyKeyboardMarkup(True)

    if question_id < len(questions):
        question = questions[question_id]
        if 'options' in question:
            keyboard.row(*question['options'])
        # add reset button
        keyboard.row(RESET_MESSAGE)

        bot.send_message(user_id, markup(question['question']), reply_markup=keyboard)

        if 'image' in question:
            # upload image to telegram servers and send it
            with open(question['image'], 'rb') as image:
                bot.send_photo(user_id, image)
    else:
        progress.pop(user_id)


def check_answer(user_id: int, answer: str):
    question_id = progress[user_id]
    if question_id < len(questions):
        question = config['questions'][question_id]

        time.sleep(random.randrange(1, 3))

        if answer.upper().strip() == question['answer'].upper():
            progress[user_id] += 1
            if progress[user_id] < len(questions):
                bot.send_message(user_id, markup(question.get('correct_msg', config.get('correct_msg', 'Правильно!'))))
                send_question(user_id)
            else:
                keyword = ReplyKeyboardMarkup(True)
                keyword.row(RESET_MESSAGE)
                bot.send_message(user_id, markup(config['end_msg']), reply_markup=keyword)
                if 'end_image' in config:
                    # upload image to telegram servers and send it
                    with open(config['end_image'], 'rb') as image:
                        bot.send_photo(user_id, image)

                progress.pop(user_id)
        else:
            bot.send_message(user_id, markup(question.get('incorrect_msg', config.get('incorrect_msg', 'Неправильно!'))))


@bot.message_handler(commands=['start'])
@bot.message_handler(regexp=RESET_MESSAGE)
def start_game(message: Message):
    user_id = message.chat.id
    bot.send_message(user_id, markup(config['start_msg'] % message.from_user.first_name), reply_markup=ReplyKeyboardRemove())
    progress[user_id] = 0
    send_question(user_id)


@bot.message_handler(content_types=['text'])
def echo(message: Message):
    user_id = message.chat.id
    if user_id in progress:
        check_answer(user_id, message.text)
    else:
        bot.send_message(user_id, markup('Напиши /start, чтобы начать!'))


if __name__ == '__main__':
    bot.infinity_polling()
