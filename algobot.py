#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from algosdk import account, mnemonic
from algosdk.v2client import algod
from telegram import (ReplyKeyboardMarkup, InlineKeyboardButton,  InlineKeyboardMarkup)
import time
import os

from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    Filters,
    ConversationHandler,
    PicklePersistence,
)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# PORT = int(os.environ.get('PORT', 5000))
TOKEN = os.environ.get('BOT_TOKEN')
url = os.environ.get('API_URL_V2')
algod_token = os.environ.get('ALGODTOKEN')

reply_keyboard = [
    ['/Create_account', '/Get_Mnemonics_from_pky'],
    ['/Query_account_balance', '/Account_status', '/enquire'],
    ['/About', '/help', '/Done'],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def connect():
    # Using the third party API
    algod_url = url  # os.environ.get('API_URL_V1')
    algod_auth = algod_token  # os.environ.get('ALGODTOKEN')
    headers = {"X-API-Key": algod_token}
    try:
        return algod.AlgodClient(algod_auth, algod_url, headers)
    except Exception as e:
        print(e)

algod_client = connect()


def start(update, context):
    user = update.message.from_user
    reply = "Hi {}! I am ALGOMessenger.".format(user['first_name'])
    reply += (
        "I can help you with a few things.\n"
        "Tell me what you need to do.\nThey should be from the menu.\n"
        "\nSend: \n"
        "/Create_account to Create an account.\n"
        "/Get_Mnemonic_from_pky to Get Mnemonic words from private key.\n"
        "/Transfer to Transfer asset.\n"
        "/Balance to Query account balance.\n"
        "/Account_status to Check your account status.\n"
        "Send /Done to cancel conversation."
        "Use /start to test this bot."
    )
    update.message.reply_text(reply, reply_markup=markup)
    context.user_data.clear()
    print(context.user_data)


def end_chat(update, context):
    update.message.reply_text(
        "Your current session is terminated.\n"
        "Click /start to restart."
    )
    return ConversationHandler.END


def wait_for_confirmation(update, context, client, txid):
    """Utility function to wait until the transaction is
    confirmed before proceeding."""
    last_round = algod_client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation...")
        last_round += 1
        # status = algod_client.status_after_block(last_round)
        txinfo = algod_client.pending_transaction_info(txid)
    return txinfo


def account_status(update, context):
    """

    :param update: Telegram's default param
    :param context: Telegram's default param
    :param address: 32 bytes Algorand's compatible address
    :return: Address's full information
    """
    pk = context.user_data['default_pk']
    status = algod_client.account_info(pk)
    for key, value in status.items():
        update.message.reply_text("{} : {}".format(key, value))
        time.sleep(0.7)
    return ConversationHandler.END


def create_account(update, context):
    """
    Returns the result of generating an account to user:
        - An Algorand address
        - A mnemonic seed phrase
    """
    update.message.reply_text("Hang on while I get you an account ...")
    time.sleep(2)
    sk, pk = account.generate_account()
    update.message.reply_text("Your address:   {}\nPrivate Key:    {}\n".format(pk, sk))
    update.message.reply_text(
        "Keep your mnemonic phrase from prying eyes.\n"
        "\nI do not hold or manage your keys."
    )
    context.user_data['default_sk'] = sk
    context.user_data['default_pk'] = pk
    if context.user_data.get('default_pk') == pk and context.user_data['default_sk'] == sk:
        update.message.reply_text("Account creation success.")
    else:
        update.message.reply_text('Account creation error\n.')
    print(context.user_data)
    time.sleep(1.5)
    update.message.reply_text('To test if your address works fine, copy your address, and visit:\n ')
    keyboard = [[InlineKeyboardButton(
        "DISPENSER", 'https://bank.testnet.algorand.network/', callback_data='1')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('the dispenser to get some Algos', reply_markup=reply_markup)

    update.message.reply_text("Session ended. Click /start to begin.")
    return ConversationHandler.END


def get_mnemonics_from_sk(update, context):
    """
    Takes in private key and converts to mnemonics
    :param context:
    :param update:
    :return: 25 mnemonic words
    # """
    sk = context.user_data['default_sk']
    print(sk)
    phrase = mnemonic.from_private_key(sk)
    update.message.reply_text(
        "Your Mnemonics:\n {}\n\nKeep your mnemonic phrase from prying eyes.\n"
        "\n\nI do not hold or manage your keys.".format(phrase), reply_markup=markup
    )
    update.message.reply_text('\nSession ended.')
    return ConversationHandler.END


def query_balance(update, context):
    pk = context.user_data['default_pk']
    print(pk)
    update.message.reply_text("Getting the balance on this address ==>   {}.".format(pk))
    if len(pk) == 58:
        account_bal = algod_client.account_info(pk)['amount']
        update.message.reply_text("Balance on your account: {}".format(account_bal))
    else:
        update.message.reply_text("Wrong address supplied.\nNo changes has been made.")
        context.user_data.clear()
    return ConversationHandler.END


def enquire(update, context):
    keyboard = [[InlineKeyboardButton("Website", 'https://algorand.com', callback_data='1'),
                 InlineKeyboardButton("Developer'site", 'https://developer.algorand.org', callback_data='2')],

                [InlineKeyboardButton("Community", 'https://community.algorand.com', callback_data='3')]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text('Learn more about Algorand:', reply_markup=reply_markup)


def button(update, context):
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    query.edit_message_text(text="Selected option: {}".format(query.data))


def help_command(update, context):
    update.message.reply_text("Use /start to test this bot.")


def done(update, context):
    # call_transfer = transfer(update, context)
    # update.message.reply_text("{}".format(call_transfer))
    if 'choice' in context.user_data:
        del context.user_data['choice']
        context.user_data.clear()
        return ConversationHandler.END
    update.message.reply_text(
        "Swift! Your transaction is completed,", reply_markup=markup
    )
    return ConversationHandler.END


def main():
    # Create the Updater and pass it your bot's token.
    pp = PicklePersistence(filename='reloroboty')
    updater = Updater(TOKEN, persistence=pp, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('Create_account', create_account))
    dp.add_handler(CommandHandler('Get_Mnemonics_from_pky', get_mnemonics_from_sk))
    dp.add_handler(CommandHandler('Query_account_balance', query_balance))
    dp.add_handler(CommandHandler('Account_status', account_status))
    dp.add_handler(CommandHandler('Done', end_chat))
    dp.add_handler(CommandHandler('About', enquire))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CommandHandler('help', help_command))
    dp.add_handler(CommandHandler('enquire', enquire))

    # dp.add_handler(CommandHandler('Address', query_balance))
    # dp.add_handler(conv_handler)
    # show_data_handler = CommandHandler('show_data', show_data)
    # dp.add_handler(show_data_handler)

    # Start the Bot
    updater.start_polling()
    # updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN)
    # updater.bot.setWebhook('https://algotelbot.herokuapp.com/' + TOKEN)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
