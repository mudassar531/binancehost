from flask import Flask
import telebot
from binance.client import Client
from datetime import datetime, timedelta

# Flask setup
app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, Binance PnL Bot is Running!"

# Replace with your actual API keys
binance_api_key = 'Ueq3zkG9hDGKYOFDKNHqQWG5iJ11W4PXwOnXf8GpCFvqPBP9q4s15xNX3kFhKAxE'
binance_api_secret = 'SPW55GDMy32JuqE481qpdcODNPRT6Za6qNW4OEol4dKVhGIDJsMzgv0eryBdg3FF'
telegram_bot_token = '7249610741:AAFYx7CG8uUq5C0vaLta1OWHqdVyQVwPhqA'

client = Client(binance_api_key, binance_api_secret)
bot = telebot.TeleBot(telegram_bot_token)

def fetch_trades(symbol, start_time, end_time):
    trades = []
    current_time = start_time
    for _ in range((end_time - start_time).days):
        next_end_time = min(current_time + timedelta(days=1), end_time)
        try:
            fetched_trades = client.get_my_trades(
                symbol=symbol,
                startTime=int(current_time.timestamp() * 1000),
                endTime=int(next_end_time.timestamp() * 1000),
                limit=1000
            )
            trades.extend(fetched_trades)
            if next_end_time >= end_time:
                break
            current_time = next_end_time
        except Exception as e:
            return f"Error fetching trades: {e}"
    return trades

def get_pnl(days, coin='BTC', base_coin='USDT'):
    if coin == base_coin:
        return "Coin and base coin cannot be the same."

    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    total_profit = 0.0
    total_loss = 0.0
    trades_history = []

    try:
        symbol = f"{coin}{base_coin}"

        trades = fetch_trades(symbol, start_time, end_time)

        if isinstance(trades, str):
            return trades

        if not trades:
            return f"No trades found for {symbol} in the past {days} days."

        for trade in trades:
            qty = float(trade['qty'])
            price = float(trade['price'])
            trade_time = datetime.fromtimestamp(trade['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            if trade['isBuyer']:
                total_loss += qty * price
                trades_history.append({
                    'type': 'Buy',
                    'amount': qty,
                    'price': price,
                    'time': trade_time
                })
            else:
                total_profit += qty * price
                trades_history.append({
                    'type': 'Sell',
                    'amount': qty,
                    'price': price,
                    'time': trade_time
                })

        net_pnl = total_profit - total_loss
        return net_pnl, total_profit, total_loss, trades_history
    except Exception as e:
        return f"Error fetching PnL data: {e}"

def format_trade_history(trades_history):
    formatted_history = []
    for trade in trades_history:
        formatted_trade = (
            f"{trade['time']} - {trade['type']} {trade['amount']:.8f} "
            f"at {trade['price']:.2f}"
        )
        formatted_history.append(formatted_trade)
    return "\n".join(formatted_history[:10])

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(text='1 Day PnL', callback_data='pnl_1'),
        telebot.types.InlineKeyboardButton(text='3 Day PnL', callback_data='pnl_3'),
        telebot.types.InlineKeyboardButton(text='7 Day PnL', callback_data='pnl_7')
    )
    markup.add(
        telebot.types.InlineKeyboardButton(text='30 Day PnL', callback_data='pnl_30'),
        telebot.types.InlineKeyboardButton(text='60 Day PnL', callback_data='pnl_60')
    )
    bot.send_message(
        message.chat.id,
        "👋 Welcome! Select a timeframe to get your Binance PnL details:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('pnl_'))
def callback_pnl(call):
    days = int(call.data.split('_')[1])
    coin = 'BTC'
    base_coin = 'USDT'
    pnl_result = get_pnl(days, coin, base_coin)
    
    if isinstance(pnl_result, str):
        reply_text = pnl_result
    else:
        net_pnl, total_profit, total_loss, trades_history = pnl_result
        trades_history_text = format_trade_history(trades_history)
        reply_text = (f"<b>Binance PnL details of {days} days ({coin}/{base_coin}):</b>\n\n"
                      f"Net PnL: {net_pnl:.2f} {base_coin}\n"
                      f"Total Profit: {total_profit:.2f} {base_coin}\n"
                      f"Total Loss: {total_loss:.2f} {base_coin}\n\n"
                      f"<b>Trade History (latest 10):</b>\n{trades_history_text}\n"
                      f"...\n")
    
    bot.send_message(call.message.chat.id, reply_text, parse_mode='HTML')

# Start polling
bot.infinity_polling()

# Start the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)