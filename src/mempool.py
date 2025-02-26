import requests
from telegram.ext.callbackcontext import CallbackContext
from telegram.update import Update
from textwrap import dedent
import config

class MempoolSpaceFees:
    def __init__(self, one_block_fee: int, three_block_fee: int, six_block_fee: int) -> None:
        self.one_block_fee = one_block_fee
        self.three_block_fee = three_block_fee
        self.six_block_fee = six_block_fee

def mempool_space_fees(update: Update, context: CallbackContext):
    """
    Recommended fees from mempool space
    """
    try:
        r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/v1/fees/recommended', timeout=5)
        json = r.json()
    except:
        context.bot.send_message(chat_id=update.message.chat_id, text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return

    fees = MempoolSpaceFees(
        one_block_fee=json['fastestFee'],
        three_block_fee=json['halfHourFee'],
        six_block_fee=json['hourFee']
    )

    message = dedent(f"""
    <b>Gebühren</b>
    Ein Block (10 min): {fees.one_block_fee} sat/vbyte
    Drei Blöcke (30 min): {fees.three_block_fee} sat/vbyte
    Sechs Blöcke (60 min): {fees.six_block_fee} sat/vbyte
    """)

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='HTML')

def fee_emoji(fee: float) -> str:
    """
    Returns an emoji depending on the fee
    """
    if fee > 100:
        return '🟥'
    if fee > 30:
        return '🟧'
    if fee > 10:
        return '🟨'
    return '🟩'

def mempool_space_mempool_stats(update: Update, context: CallbackContext):
    """
    Mempool statistics from mempool space
    """

    try:
        r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/mempool', timeout=5)
        mempool = r.json()
    except:
        context.bot.send_message(chat_id=update.message.chat_id, text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return

    try:
        r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/v1/fees/mempool-blocks', timeout=5)
        blocks = r.json()
    except:
        context.bot.send_message(chat_id=update.message.chat_id, text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return

    try:
        num_blocks = int(context.args[0])
    except:
        num_blocks = 3

    if num_blocks <= 0:
        num_blocks = 1

    message = dedent(f"""
    <b>Mempool</b>
    Anzahl: {'{0:,.0f}'.format(mempool['count'])} tx
    Backlog: {mempool['vsize'] / 1_000_000:.1f} vMB
    """)

    for index, block in enumerate(blocks):
        fee_range = block['feeRange']

        try:
            min_fee = fee_range[0]
            max_fee = fee_range[-1]
        except:
            min_fee = 1.0
            max_fee = 1.0

        if index <= num_blocks - 1:
            message += dedent(f"""
            <i>Block {index+1} (In ~{(index+1) * 10} min)</i>
            {fee_emoji(max_fee)} Max: {max_fee:.1f} sat/vbyte 
            {fee_emoji(min_fee)} Min: {min_fee:.1f} sat/vbyte
            """)

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='HTML')

def blockzeit(update: Update, context: CallbackContext):
    """
    Returns the current block time (block height)
    """
    try:
        r = requests.get(f'{config.MEMPOOL_SPACE_URL}/api/blocks/tip/height', timeout=5)
        height = r.json()
    except:
        context.bot.send_message(chat_id=update.message.chat_id, text='Server nicht verfügbar. Bitte später nochmal versuchen!')
        return

    message = dedent(f"""
    <b>Aktuelle Blockzeit</b>
    {height}
    """)

    context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='HTML')
