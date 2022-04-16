import logging
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup
import bisect

class Game_board:

    def prov(s, n):
        s = str(s)
        for i in s:
            if i not in map(str, range(10)):
                return False
        if len(s) != n:
            print(2)
            return False
        if len(set(list(s))) != n:
            print(3)
            return False
        if '0' == s[0]:
            print(45)
            return False
        return True

    class Answer:

        def __init__(self, b_count=0, k_count=0):
            self.b_count = b_count
            self.k_count = k_count

        def __str__(self):
            return f'быков:{self.b_count};коров:{self.k_count}'


    def count(a, b):
        b_count = 0
        k_count = 0
        for i in range(len(a)):
            if a[i] == b[i]:
                b_count += 1
            elif a[i] in b:
                k_count += 1
        return Game_board.Answer(b_count, k_count)



class Person:

    def __init__(self, update, context):
        self.update, self.context = update, context
        self.index = None

    def free(self):
        return self.index == None

    def name(self):
        return self.update.message.chat.username

class Pair:

    def __init__(self, person1 : Person, person2: Person):
        self.person1 = person1
        self.person2 = person2
        self.persons = [self.person1, self.person2]
        self.key = f'{get_name(self.person1)}@{get_name(self.person2)}'
        self.quiz1 = None
        self.quiz2 = None
        self.queue_number = 0
        self.count_xod = 0


    # фуннкциф возрващающая противника
    def enemy(self, update):
        if self.person1.update.message.chat.username == update.message.chat.username:
            return self.person2
        if self.person2.update.message.chat.username == update.message.chat.username:
            return self.person1

    def quiz(self, update):
        if self.person1.update.message.chat.username == update.message.chat.username:
            return self.quiz2
        if self.person2.update.message.chat.username == update.message.chat.username:
            return self.quiz1

    def number(self, update):
        if self.person1.update.message.chat.username == update.message.chat.username:
            return 0
        if self.person2.update.message.chat.username == update.message.chat.username:
            return 1

    def number_queue(self, update):
        return self.number(update) == self.queue_number

    def message(self, s, update):
        self.enemy(update).update.message.reply_text(str(s))

    def __str__(self):
        return f'{self.person1.name()}:{self.person2.name()},{self.free_xod()}.{self.quiz1},{self.quiz2}'

    def xod(self, update, ans=None, text=None):
        if self.free_xod():
            self.count_xod += 1
            self.queue_number += 1
            self.queue_number %= 2
            self.message(f'Ход Вашего противника {text}: {str(ans)}', update)

    def finish(self):
        if self.count_xod % 2 == 0:
            self.person2.update.message.reply_text('Поздравляем с победой')
            self.person1.update.message.reply_text(f'Увы ВЫ проиграли, Ваш противник загадал число {self.quiz2}')
        else:
            self.person1.update.message.reply_text('Поздравляем с победой')
            self.person2.update.message.reply_text(f'Увы ВЫ проиграли, Ваш противник загадал число {self.quiz1}')

    def free_xod(self):
        return self.quiz1 != None and self.quiz2 != None

    def put_quiz(self, update, quiz):
        if get_name(self.person1) == get_name(update) and self.quiz1 == None:
            self.quiz1 = quiz
        if get_name(self.person2) == get_name(update) and self.quiz2 == None:
            self.quiz2 = quiz

        if self.free_xod():
            self.person1.update.message.reply_text('игра началась Ваша очередь')
            self.person2.update.message.reply_text('игра началась ждём когда первый игрок сходит')




def get_name(update):
    if type(update) == Person:
        return update.update.message.chat.username
    return update.message.chat.username


class Game_info:

    def __init__(self):
        self.free = True
        self.free_name = None
        self.key = 0
        self.persons = dict()
        self.pairs = dict()
        self.N = 4

    def put(self, update, context):
        self.free = False
        self.free_name = self.person_get(update)
        self.person_get(update).index = None

    def find_game(self, update, context):
        person = self.free_name
        person_new = Person(update, context)
        self.free = True
        self.free_name = None
        self.find_game_message(person)
        self.find_game_message(person_new)
        self.append_pair(person, person_new)

    def find_game_message(self, person):
        person.update.message.reply_text('Игра найдена')

    def person_put_game(self, person1, person2):
        self.persons[get_name(person1)].index = person2

    def append_pair(self, person1, person2):
        pair = Pair(person1, person2)
        self.pairs[pair.key] = pair
        self.person_put_game(person1, pair.key)
        self.person_put_game(person2, pair.key)

    def append_person(self, update, context):
        if get_name(update) not in self.persons:
            self.persons[get_name(update)] = Person(update, context)
        return Person(update, context)

    def person_free(self, update):
        return self.person_get(update).free()

    def person_get(self, update, contex=None):
        return self.persons.get(get_name(update), self.append_person(update, contex))

    def person_get_game(self, update):
        return self.person_get(update)

    def person_put_free(self, update):
        self.persons[get_name(update)].index = None

    def person_key(self, update):
        return self.persons[get_name(update)].index

    def get_pair(self, update):
        return self.pairs[self.person_key(update)]

    def pair_quiz(self, update):
        self.get_pair(update).quiz(update)

    def pair_queue_number(self, update):
        return self.get_pair(update).number_queue(update)

    def pair_xod(self, update):
        self.pairs[self.person_key(update)].xod(update)

    def pair_finish(self, update):
        self.get_pair(update).finsh()
        self.person_put_free(self.get_pair(update).person1)
        self.person_put_free(self.get_pair(update).person2)
        del self.pairs[self.person_key(update)]

    def pair_free_xod(self, update):
        self.get_pair(update).free_xod()

    def pair_put_quiz(self, update, text):
        self.pairs[self.person_key(update)].put_quiz(update, text)




INFO = Game_info()
markup_start = ReplyKeyboardMarkup([['/go']], one_time_keyboard=False)
def start(update, context):
    global INFO
    INFO.append_person(update, context)
    update.message.reply_text(f'''
   Это бот "игра Быки и коровы"!
Правила игры: https://urok.1sept.ru/articles/662278
Мы играем с {INFO.N} цифрами в числе.
Чтобы начать – команда /go
Когда игра будет найдена, введите загадываемое число
потом Вы со своим противником будете по очереди пытаться отгадать число; выигрывает тот, кто первый отгадает.
Удачной игры
    ''',
                              reply_markup=markup_start
                              )
def go(update, context):
    global INFO
    if INFO.person_free(update):
        update.message.reply_text('Ищем соперника',
                                  reply_markup=markup_start
                                  )
        if INFO.free:
            INFO.put(update, context)
            INFO.free = False
        else:
            INFO.find_game(update, context)
    else:
        update.message.reply_text(f'Вы уже играете с {get_name(INFO.get_pair(update).enemy(update))}')

def text_handler(update, context):
    global INFO
    if not INFO.person_free(update):
        if INFO.pair_free_xod(update):
            if INFO.pair_queue_number(update):
                if Game_board.prov(update.message.text, INFO.N):
                    update.message.reply_text('ход сделан')
                    ans = Game_board.count(update.message.text, INFO.pair_quiz(update))
                    if ans.b_count == INFO.N:
                        update.message.reply_text('Вы выиграли')
                        INFO.pair_finish(update)
                    else:
                        update.message.reply_text(str(ans))
                        INFO.pair_xod(update, str(ans), update.message.text)
                else:
                    update.message.reply_text('Некоректный запрос')

            else:
                update.message.reply_text('Не Ваша очерердь')
        else:
            if Game_board.prov(update.message.text, INFO.N):
                INFO.pair_put_quiz(update, update.message.text)
                update.message.reply_text(f'Вы загодали{update.message.text}')
            else:
                update.message.reply_text('Некоректное загадываемое число')
    else:
        pass





class Driver:

    def __init__(self):
        pass

    def prob(self, update, context):
        global INFO
        INFO.append_person(update, context)
        context.bot_data['a'] = context.bot_data.get('a', 0) + 1
        print(context.bot_data)
        print(update.message.chat.username)

    def save(self, update, context):
        context.bot_data['INFO'] = INFO

    def get(self, update, context):
        global INFO
        INFO = context.bot_data['INFO']

    def info(self, update, context):
        for i in INFO.pairs:
            update.message.reply_text(f'{i}:{INFO.pairs[i]}')

    def clear(self, update, context):
        global INFO
        INFO = Game_info()


TOKEN = '5123580062:AAEcL4kGPRRPdZLhUlOzYe-xzKIl8OYTmrg'
def main():
    updater = Updater(TOKEN)
    driver = Driver()
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("go", go))
    dp.add_handler(CommandHandler("prob", driver.prob))
    dp.add_handler(CommandHandler("save", driver.save))
    dp.add_handler(CommandHandler("get", driver.get))
    dp.add_handler(CommandHandler("info", driver.info))
    dp.add_handler(CommandHandler("clear", driver.clear))
    dp.add_handler(MessageHandler(Filters.text, text_handler))
    updater.start_polling()
    updater.idle()

main()
