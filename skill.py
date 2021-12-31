# coding: utf-8
from __future__ import unicode_literals

import codecs
import pickle
import random
import logging
import akinator

logging.getLogger().setLevel(logging.DEBUG)

suggests = [
    {'title': "Да", 'hide': True},
    {'title': "Нет", 'hide': True},
    {'title': "Я не знаю", 'hide': True},
    {'title': "Наверно", 'hide': True},
    {'title': "Наверно нет", 'hide': True},
    {'title': "Назад", 'hide': True}
]

tts_effect = [
    "megaphone",
    "train_announce"
]


def handler(event, context):
    response = {
        "version": event['version'],
        "session": event['session'],
        "response": {
            "end_session": False
        }
    }

    handle_dialog(event, event['state'], response)

    logging.debug('Response: %r', response)

    return response


def handle_dialog(req, state, res):
    """Функция для непосредственной обработки диалога."""

    aki = None
    state = state.get('session')

    # Обрабатываем новичка.
    if req['session']['new'] or not state:
        aki = akinator.Akinator()
        _hi = "Это игра где я попытаюсь угадать персонажа, которого вы загадали. Итак, начнем: "
        # TODO: можно вытягивать локаль!
        res['response']['text'] = _hi + aki.start_game(language='ru')
        res['response']['buttons'] = suggests
        res['session_state'] = {
            'a': codecs.encode(pickle.dumps(aki), "base64").decode(),
            'complete': False
        }
        return

    aki = pickle.loads(codecs.decode(state['a'].encode(), "base64"))

    # Обрабатываем ответ пользователя.
    user_ans = normalize_answer(req['request']['original_utterance'].lower())
    logging.debug('Answer code: %r', user_ans)

    _progression = aki.progression
    if _progression > 80 and not state['complete']:
        state['complete'] = True
        first_guess = aki.win()
        _name = first_guess['name']
        _desc = first_guess['description']
        res['response']['text'] = f'Это {_name}, {_desc}! Правильно?'
        res['response']['buttons'] = suggests[:2]
        res['session_state'] = state
        return

    if user_ans is not None:
        if state['complete']:
            if user_ans == 0:
                res['response']['text'] = 'Вау, отлично! Спасибо за игру.'
                res['response']['end_session'] = True
                return
            elif user_ans == 1:
                _text = 'Ну вот... В следующий раз я подготовлюсь лучше! Спасибо за игру.'
                res['response']['text'] = _text
                res['response']['end_session'] = True
                return
            else:
                res['response']['text'] = 'Я не поняла... Переформулируйте ответ.'
                res['response']['buttons'] = suggests[:2]
        else:
            if user_ans == -1:
                try:
                    res['response']['text'] = aki.back()
                    res['response']['buttons'] = suggests
                except:
                    _ans = aki.question
                    res['response']['text'] = 'Некуда возвращаться... ' + _ans
                    res['response']['buttons'] = suggests
            elif user_ans == -2:
                _question = aki.question
                res['response']['text'] = _question
                _e = random.choice(tts_effect)
                res['response']['tts'] = f'<speaker effect="{_e}">{_question}'
                res['response']['buttons'] = suggests
            else:
                res['response']['text'] = aki.answer(
                    user_ans)
                res['response']['buttons'] = suggests
    else:
        res['response']['text'] = 'Я не поняла... Переформулируйте ответ.'
        res['response']['buttons'] = suggests
    state['a'] = codecs.encode(pickle.dumps(aki), "base64").decode()
    res['session_state'] = state


def normalize_answer(ans):
    """Нормализуем ответ пользователя к параметру акинатора."""
    logging.debug('Answer: %r', ans)
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
