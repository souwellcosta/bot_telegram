import telebot
import requests
import time
from telebot import types
from gerencianet import Gerencianet
from twilio.rest import Client

# Replace this with your actual Telegram bot token
TOKEN = "7622104238:AAGUUSQ8IPMCfHXXM--68y8UXZAbJBcMVfs"
bot = telebot.TeleBot(TOKEN)

# Configurações do Gerencianet
CREDENTIALS = {
    "client_id": "1e38bfa034b0bd86f8775a5f5580bcf7ac4082ae",
    "client_secret": "ac1775e8477f3b6784faef7530108e1775759299",
    "sandbox": True
}
gn = Gerencianet(CREDENTIALS)

# Configurações do Twilio
TWILIO_ACCOUNT_SID = "SK77c4e3c816127ca1033d6e46b6f3719e"
TWILIO_AUTH_TOKEN = "SYHuxGpIrjMOSyURzi8QS5I3EdGUIs8y"
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

PACOTES = {
    1: 0.50,
    3: 1.50,
    5: 2.50
}

# Comando /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "Olá! 👋 Bem-vindo ao nosso bot de números virtuais.\n\n📲 Aqui você pode comprar números temporários para ativação de serviços. Escolha um dos pacotes abaixo:")
    escolher_quantidade(message)

# Comando /comprar
@bot.message_handler(commands=['comprar'])
def escolher_quantidade(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for qtd, valor in PACOTES.items():
        markup.add(f"{qtd} números - ${valor:.2f}")
    
    bot.send_message(message.chat.id, "💳 Escolha a quantidade de números que deseja comprar:", reply_markup=markup)

@bot.message_handler(func=lambda message: any(str(qtd) in message.text for qtd in PACOTES.keys()))
def processar_compra(message):
    qtd = int(message.text.split()[0])
    valor = PACOTES[qtd]

    # Gerar QR Code PIX
    txid, qrcode = gerar_qr_pix(valor, message.chat.id)
    bot.send_message(message.chat.id, "💰 Escaneie o QR Code abaixo para realizar o pagamento:")
    bot.send_photo(message.chat.id, qrcode)

    # Verificar pagamento
    bot.send_message(message.chat.id, "🔄 Aguardando pagamento...")
    for _ in range(20):
        if verificar_pagamento(txid):
            numeros = obter_numeros_virtuais(qtd)
            bot.send_message(message.chat.id, f"✅ Pagamento confirmado! Seus números são: {', '.join(numeros)}")
            return
        time.sleep(30)

    bot.send_message(message.chat.id, "⏳ Pagamento não confirmado dentro do prazo. Tente novamente.")

# Função para Gerar QR Code PIX
def gerar_qr_pix(valor, user_id):
    payload = {
        "calendario": {"expiracao": 3600},
        "valor": {"original": f"{valor:.2f}"},
        "chave": "ff1776b4-4251-4261-bf4a-6c420dae0c08",  # Adicionei sua chave Pix aqui
        "solicitacaoPagador": "Pagamento pelo bot"
    }

    response = gn.pix_create_immediate_charge({}, payload)
    txid = response["txid"]

    qrcode = gn.pix_generate_qrcode(txid)
    return txid, qrcode["imagemQrcode"]

# Função para Verificar Pagamento
def verificar_pagamento(txid):
    resposta = gn.pix_detail_charge(txid)
    return resposta["status"] == "CONCLUIDA"

# Função para Obter os Números Virtuais com Twilio
def obter_numeros_virtuais(qtd):
    numeros = []
    for _ in range(qtd):
        # Compre um número do Twilio
        number = twilio_client.incoming_phone_numbers.create(
            phone_number='+1XXX5550100'  # Adapte para o número desejado
        )
        numeros.append(number.phone_number)

    return numeros

# Iniciar o Bot
if __name__ == "__main__":
    print("Bot is running...")
    bot.polling(none_stop=True)
