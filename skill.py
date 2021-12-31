# coding: utf-8
"""
Демонстрация навыка для Алисы где она будет угадывать персонажа.
"""
from __future__ import unicode_literals

import json
import logging
import akinator
import random

from flask import Flask, request
app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

# Сессии
sessionStorage = {}
# Стандартные ответы
suggests = [
    {'title': "Да", 'hide': True},
    {'title': "Нет", 'hide': True},
    {'title': "Я не знаю", 'hide': True},
    {'title': "Наверно", 'hide': True},
    {'title': "Наверно нет", 'hide': True},
    {'title': "Назад", 'hide': True}
]
# Эффекты для повторения вопроса
tts_effect = [
    "megaphone",
    "train_announce"
]


@app.route("/", methods=['GET'])
def index():
    """Чек."""
    return "OK"


@app.route("/", methods=['POST'])
def handler():
    """Маппинг запроса навыка."""
    logging.info('Request: %r', request.json)

    response = {
        "version": request.json['version'],
        "session": request.json['session'],
        "response": {
            "end_session": False
        }
    }

    handle_dialog(request.json, response)

    logging.info('Response: %r', response)

    return json.dumps(
        response,
        ensure_ascii=False,
        indent=2
    )


def handle_dialog(req, res):
    """Функция для непосредственной обработки диалога."""

    user_id = req['session']['user_id']

    # Обрабатываем новичка.
    if req['session']['new'] or user_id not in sessionStorage:
        sessionStorage[user_id] = {
            'a': akinator.Akinator(),
            'has_complete': False
        }
        _hi = "Это игра где я попытаюсь угадать персонажа, которого вы загадали. Итак, начнем: "
        res['response']['text'] = _hi + sessionStorage[user_id]['a'].start_game(
            language='ru')
        res['response']['buttons'] = suggests
        return

    # Обрабатываем ответ пользователя.
    user_ans = normalize_answer(req['request']['original_utterance'].lower())
    logging.debug('Answer code: %r', user_ans)

    _progression = sessionStorage[user_id]['a'].progression
    _has_complete = sessionStorage[user_id]['has_complete']
    if _progression > 80 and not _has_complete:
        sessionStorage[user_id]['has_complete'] = True
        first_guess = sessionStorage[user_id]['a'].win()
        _name = first_guess['name']
        _desc = first_guess['description']
        res['response']['text'] = f'Это {_name}, {_desc}! Правильно?'
        res['response']['buttons'] = suggests[:2]
        return

    if user_ans is not None:
        if sessionStorage[user_id]['has_complete']:
            if user_ans == 0:
                res['response']['text'] = 'Вау, отлично! Спасибо за игру.'
                res['response']['end_session'] = True
                del sessionStorage[user_id]
            elif user_ans == 1:
                _text = 'Ну вот... В следующий раз я подготовлюсь лучше! Спасибо за игру.'
                res['response']['text'] = _text
                res['response']['end_session'] = True
                del sessionStorage[user_id]
            else:
                res['response']['text'] = 'Я не поняла... Переформулируйте ответ.'
                res['response']['buttons'] = suggests[:2]
        else:
            if user_ans == -1:
                try:
                    res['response']['text'] = sessionStorage[user_id]['a'].back()
                    res['response']['buttons'] = suggests
                except:
                    _ans = sessionStorage[user_id]['a'].question
                    res['response']['text'] = 'Некуда возвращаться... ' + _ans
                    res['response']['buttons'] = suggests
            elif user_ans == -2:
                _question = sessionStorage[user_id]['a'].question
                res['response']['text'] = _question
                _e = random.choice(tts_effect)
                res['response']['tts'] = f'<speaker effect="{_e}">{_question}'
                res['response']['buttons'] = suggests
            else:
                res['response']['text'] = sessionStorage[user_id]['a'].answer(
                    user_ans)
                res['response']['buttons'] = suggests
    else:
        res['response']['text'] = 'Я не поняла... Переформулируйте ответ.'
        res['response']['buttons'] = suggests


def normalize_answer(ans):
    """Нормализуем ответ пользователя к параметру акинатора."""
    logging.info('Answer: %r', ans)
    if ans in [
        "повтори",
        "еще раз",
        "повтори вопрос",
        "что"
    ]:
        return -2
    if ans in [
        "предыдущий вопрос",
        "назад",
        "вернись"
    ]:
        return -1
    if ans in [
        "да",
        "точно",
        "ага",
        "именно"
    ]:
        return 0
    if ans in [
        "не",
        "нет",
        "неа",
        "неверно"
    ]:
        return 1
    if ans in [
        "хз",
        "я не знаю",
        "не знаю",
        "без понятия",
        "кто знает"
    ]:
        return 2
    if ans in [
        "наверно",
        "наверноe",
        "быть может",
        "может быть",
        "кто знает",
        "очень может быть",
        "пожалуй",
        "скорее всего",
        "скорее всего да"
    ]:
        return 3
    if ans in [
        "наврятли",
        "наверно нет",
        "скорее всего нет",
        "нет наверное"
    ]:
        return 4
    return None


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True, port=14753)
