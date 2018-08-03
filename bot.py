from telegram.ext import Updater, CommandHandler, Filters, MessageHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import logging, requests, redis

r = redis.StrictRedis(host='localhost', port=6380, db=0)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

SERVICE_URL = 'https://exa/Service/'

updater = Updater('37773234117417:AAFjV2xyj6MCpkjQ0klfmswwf9GfecY5wfwDhzPfddz-ASQ')
main_custom_keyboard = [['ورود به حساب'], ['ثبت سفارش'],
                   ['اطلاعات بیشتر', 'پشتیبانی'],
                   ]

def is_logged_in(bot, update):

    if r.hmget(update.message.chat_id, 'user_token')!= None:
        my_token = r.hmget(update.message.chat_id, 'user_token')[0]
        is_login = requests.get(SERVICE_URL + 'service/is_authorized', headers={'Authorization': 'Bearer ' + str(my_token)})

        if is_login.status_code == 400:
            return False

        elif is_login.status_code == 200:
            return True
    else:
        return False


def get_my_cash(update):

        my_token = r.hmget(update.message.chat_id, 'user_token')[0].decode('utf8')
        res = requests.get(SERVICE_URL + 'service/myprofile', headers={'Authorization': 'Bearer ' + str(my_token)})

        if res.status_code == 400:
            return False

        elif res.status_code == 200:
            return res.json()['cash'] + "تومان"


def return_sutable_main_menu(bot, update):
    if is_logged_in(bot, update):
        replay_custom_keyboard = [
                                  [' خروج از حساب','کیف پول'], ['ثبت سفارش'],
                                  ['اطلاعات بیشتر', 'پشتیبانی']
                                 ]
    else:
        replay_custom_keyboard = main_custom_keyboard

    return ReplyKeyboardMarkup(replay_custom_keyboard)


def pay(amount):
    #todo:check for amount is number

    my_token = r.get('user_token').decode('utf8')
    #temprory disable this for avoid spam data /create_pay_rial
    #res = requests.post(SERVICE_URL + 'service/', data={"amount": amount}, headers={'Authorization': 'Bearer ' + str(my_token)})
    status_code=200#res.status_code
    if status_code == 400:
        return "لطفا دوباره وارد حساب خود شوید"

    elif status_code == 200:
        order_id = '23'#(res.text)
        if order_id == '0':
            return  ("خطایی در ایجاد تراکنش ایجاد گردید ")
        elif order_id == '-2':
            return ("حداقل مبلغ باید  50،000 ريال باشد لطفا دوباره مبلغ را وارد نماییید")
        else:
            return '<a href="http://exo.com/redirectSEP.aspx?pid='+order_id+'>پرداخت</a>'




def start(bot, update):
    r.hmset(update.message.chat_id, {'bot_status': 'started'})
    bot.send_message(update.message.chat_id, text="سلام "+str(update.message.from_user.first_name)+" "+str(update.message.chat_id)+"عزیز ", reply_markup=return_sutable_main_menu(bot, update))


def stop(bot, update):
    r.hmset(update.message.chat_id, {'bot_status': 'stopped'})
    update.message.reply_text('بات برای شما غیر فعال شد. 😔')
    updater.stop()

def major(bot, update):
    temp = r.hmget(update.message.chat_id, 'bot_status')[0]
    if temp == b"started":

        result = update.message.text
        if result == 'اطلاعات بیشتر':
             bot.send_message(update.message.chat_id, text='<a href="https://exo.com"> برای اطلاعات بیشتر به وبسایتمون سر بزنید</a>', parse_mode=ParseMode.HTML)
             r.set('loc', '')  # reset it
        elif result == 'پشتیبانی':
            bot.send_message(update.message.chat_id,
                             text='<b>پشتیبانی ۲۴ ساعته تلگرام : </b><a href="tg://user?id=383754959">@alochorahchi</a>',
                             parse_mode=ParseMode.HTML)
            r.hmset(update.message.chat_id, {'loc': 'main'})

        elif result == 'ورود به حساب':
            r.hmset(update.message.chat_id, {'loc': 'login_step1'})
            # todo:send new keyboard here
            bot.send_message(update.message.chat_id, text='شماره موبایلتان را وارد نمایید')
        elif result == 'خروج از حساب':
            r.hmset(update.message.chat_id, {'user_token': ''})
            bot.send_message(update.message.chat_id,
                             text="خروج با موفقیت رخ داد. " + str(update.message.from_user.first_name) + " " + str(
                                 update.message.chat_id) + "عزیز ", reply_markup=return_sutable_main_menu())




        elif result == 'کیف پول':
            # r.set('loc', 'login-step1')

            my_cash = get_my_cash()

            if my_cash != False:
                r.hmset(update.message.chat_id, {'loc': 'menu-my-cash'})

                cash_custom_keyboard = [['افزایش موجودی'], ['بازگشت'] ]
                bot.send_message(update.message.chat_id, text='موجودی کیف پول شما:'+my_cash, reply_markup=ReplyKeyboardMarkup(cash_custom_keyboard))

            else:
                # todo:send new keyboard here
                bot.send_message(update.message.chat_id, text='لطفا دوباره وارد حساب خود شوید', reply_markup=ReplyKeyboardMarkup(main_custom_keyboard))


        elif result == 'افزایش موجودی':
            r.hmset(update.message.chat_id, {'loc': 'menu-charge-cash'})
            cash_custom_keyboard = [['بازگشت'], ['5000', '100000', '150000', '200000']]
            bot.send_message(update.message.chat_id, text='لطفا یکی از مقادیر ریالی زیر را انتخاب یا مقدار مبلغ را به ریال وارد نمایید',
                             reply_markup=ReplyKeyboardMarkup(cash_custom_keyboard))


        elif result == 'ثبت سفارش':
            r.hmset(update.message.chat_id, {'loc': 'menu-mahsulat'})
            get_data = requests.get(SERVICE_URL+'service/Fetchin_products')
            products = get_data.json()
            s = []
            b = ['بازگشت']
            for x in products:
                    l=[]
                    l.append(str(x['product_id'])+'_'+x['product_name']+'_'+str(x['price']/10)+' تومان ')
                    s.append(l)
            s.append(b)
            reply_markup = ReplyKeyboardMarkup(s)
            bot.send_message(update.message.chat_id, text="انتخاب کنید ", reply_markup=reply_markup)

        elif result == 'بازگشت':
            temp = r.hmget(update.message.chat_id, 'loc')

            if temp == b"menu-mahsulat" or temp == b"menu-my-cash" or temp == b"menu-charge-cash":
                bot.send_message(update.message.chat_id, text='برای ادامه از گزینه ها استفاده کنید', reply_markup=return_sutable_main_menu())


        else:
            temp = r.hmget(update.message.chat_id, 'loc')
            #GET PHONE NUMBER STEP
            if temp == b"login-step1":

                #todo:check if phone is valid and has 11 lenght or 10
                if len(result) == 11 or len(result) == 10:
                    r.hmset(update.message.chat_id, {'user_phone': result, 'loc': 'login_step1'})
                    # todo:send new keyboard here
                    bot.send_message(update.message.chat_id, text='رمز عبورتان را وارد نمایید')
                else:
                    bot.send_message(update.message.chat_id, text='شماره موبایل مجاز نیست همانند نمونه وارد نمایید 09145678910')


            elif temp == b"login-step2":
                #bot.editMessageText(chat_id=update.message.chat_id,message_id=update.message.message_id,text='*')
                #r.set('user_password', result) #no need to save it in last step
                get_auth = requests.post(SERVICE_URL+'user/login',
                                         data={"username": r.hmget(update.message.chat_id, 'user_phone'), "password": result,
                                               "grant_type": "password"})

                if get_auth.status_code == 400:
                    bot.send_message(update.message.chat_id, text='شماره موبایل یا رمز نا درست میباشد موبایل حتما به انگلیسی وارد شود')

                elif get_auth.status_code == 200:
                    r.hmset(update.message.chat_id, {'user_token': get_auth.json()['access_token'], 'bot_status': '', 'loc': 'loged_in', 'user_phone': '', 'password': ''})
                    # todo:send new keyboard here
                    bot.send_message(update.message.chat_id, text='ورود موفق!', reply_markup=return_sutable_main_menu())

            #get user entered amount for charge
            elif temp == b"menu-charge-cash":
                res = pay(result)
                bot.send_message(update.message.chat_id, text=res, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            r.hmset(update.message.chat_id, {'loc': 'charge_cash'})

            #elif temp == b"menu-mahsulat":
              #  bot.send_message(update.message.chat_id, text="not implemented yet")
                #r.set('loc', '')  # reset it
    else:
        bot.send_message(update.message.chat_id, text='بات غیر فعال است برای فعال سازی از /start استفاده کنید ', parse_mode=ParseMode.HTML)


updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('stop', stop))
updater.dispatcher.add_handler(MessageHandler([Filters.text], major))

updater.start_polling()
updater.idle()
