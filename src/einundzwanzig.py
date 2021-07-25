from telegram import Update
import requests
from bs4 import BeautifulSoup
from telegram.chat import Chat
from telegram.ext.callbackcontext import CallbackContext
from textwrap import dedent
import json
import config
import qrcode
import os
import logging

# Define podcast formats
urlAll = '/podcast/'
urlNews = '/podcast/news/'
urlLese = '/podcast/lesestunde/'
urlWeg = '/podcast/der-weg/'
urlInterviews = '/podcast/interviews/'

def getEpisode(url: str) -> str:
    """
    Returns the link to the most recent episode or an error message, if
    the request fails
    """
    try:
        r = requests.get(config.EINUNDZWANZIG_URL + url, timeout=5)
        doc = BeautifulSoup(r.text, "html.parser")
        return f"{config.EINUNDZWANZIG_URL + doc.select('.plain')[0].get('href')}"
    except:
        return "Es kann aktuell keine Verbindung zum Server aufgebaut werden. Schau doch solange auf Spotify vorbei: https://open.spotify.com/show/10408JFbE1n8MexfrBv33r"

def episode(update: Update, context: CallbackContext):
    """
    Sends a link to the most recent podcast episode
    """

    try:
        if context.args != None:
            format = str(context.args[0]).lower()
        else:
            format = "alle"
    except: 
        format = "alle"
    
    if format == "news":
        message = getEpisode(urlNews)
    elif format == "lesestunde":
        message = getEpisode(urlLese)
    elif format == "alle":
        message = getEpisode(urlAll)
    elif format == "weg":
        message = getEpisode(urlWeg)
    elif format == "interview":
        message = getEpisode(urlInterviews)
    else:
        message = 'Das ist kein gültiges Podcast-Format! Bitte gibt eins der folgenden Formate an: Alle, Interviews, Lesestunde, News, Weg'

    if update.effective_chat != None:
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def getInvoice(amt: int, memo: str) -> str:
    """
    Returns a Lightning Invoice from the Tallycoin API
    """

    TALLYDATA = {
    'type': 'fundraiser',
    'id': 'zfxqtu',
    'satoshi_amount': '21',
    'payment_method': 'ln',
    'message' : ''
    }
    
    TALLYDATA['satoshi_amount'] = str(amt)
    TALLYDATA['message'] = memo
    response = requests.post('https://api.tallyco.in/v1/payment/request/', data=TALLYDATA).text
    dict = json.loads(response)
    return dict["lightning_pay_request"]

def createQR(text: str, chatid: str):
    """
    Creates a QR Code with the given text and saves it as a png file in the current directory
    """

    img = qrcode.make(text)
    img.save(chatid + '.png')

def shoutout(update: Update, context: CallbackContext):
    """
    Returns a TallyCoin LN invoice for a specific amount that includes a memo
    """
    
    chat = update.effective_chat

    if chat != None and chat.type == Chat.PRIVATE and context.args != None:

        try:
            value = int(context.args[0])
            if value < 21_000:
                update.message.reply_text('Der Betrag muss sich auf mindestens 21.000 sats belaufen')
                return
        except:
            value_error_message = dedent(f'''
            <b>Verwendung</b>
            /shoutout betrag memo

            Bitte gib einen Betrag von mindestens 21.000 sats an.
            Das Shoutout hat eine maximale Länge von 140 Zeichen.
            ''')
            update.message.reply_text(text=value_error_message, parse_mode='HTML')
            return

        try:
            memo = ' '.join(context.args[1:])
            if len(memo) > 140:
                update.message.reply_text(text='Das Shoutout kann nicht länger als 140 Zeichen sein!')
                return
        except:
            memo = ''

        try:
            invoice = getInvoice(value, memo)
        except Exception as e:
            update.message.reply_text(text='Fehler beim Erstellen der Invoice! Bitte später noch mal versuchen.')
            logging.error(f'Error while trying to generate invoice: {e}')
            return

        try:
            createQR(invoice, str(chat.id))
        except Exception as e:
            update.message.reply_text(text='Fehler beim Erstellen des QR Codes. Bitte später noch mal versuchen.')
            logging.error(f'Error while generating QR Code: {e}')
            return

        shoutout_message = dedent(f'''
        <b>Dein Shoutout</b>
        Betrag: {value} sats
        Memo: {memo}
        ''')

        update.message.reply_text(shoutout_message, parse_mode='HTML')
        update.message.reply_photo(photo=open(f'{chat.id}.png', 'rb'), caption=str(invoice).lower())

        try:
            os.remove(f'{chat.id}.png')
        except:
            logging.error(f'QR Code file {chat.id}.png could not be deleted')

    else:
        update.message.reply_text(text=f'''
        Shoutouts können nur im direkten Chat mit dem Community Bot gesendet werden. Bitte beginne eine Konversation mit {context.bot.name}!
        ''')