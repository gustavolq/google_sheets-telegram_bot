from dotenv import load_dotenv
load_dotenv()
import os

# Pacotes para API Google Sheets 
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Pacotes para API Telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters

# Pacote para criação de logs
import logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

DATA = range(1)

# Mensagem que o usuário recebe quando encaminha /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    logger.info(f"Usuário {user.first_name} iniciou a conversa.")
    
    # update.message.reply_html = Encaminha uma mensagem em HTML
    await update.message.reply_html(rf"Olá! Seja muito bem-vindo ao Bot de controle financeiro {user.mention_html()}! Digite /help para visualizar os comandos disponíveis.")

# Mensagem que o usuário recebe quando encaminha /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    logger.info(f"Usuário {user.first_name} utilizou o comando /help.")
    await update.message.reply_html("/start : Inicia a conversa com o bot. \n/help : Verifica os comandos disponíveis. \n/update : Realiza a inserção de dados na planilha.")

# Mensagem que o usuário recebe quando encaminha uma mensagem que não é um comando
async def non_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message, user = update.message.text, update.message.from_user
    logger.info(f"Usuário {user.first_name} encaminhou a mensagem '{message}' e não foi encontrado nenhum comando.")
    await update.message.reply_html("Desculpe, eu não entendi o que você quis dizer. Digite /help para visualizar os comandos disponíveis.")

# Mensagem que o usuário recebe quando encaminha /update
async def update_sheet_command(update : Update, context: ContextTypes.DEFAULT_TYPE) -> DATA:
    user = update.message.from_user
    logger.info(f"Usuário {user.first_name} utilizou o comando /update.")
    await update.message.reply_html("Você escolheu realizar a inserção de dados na planilha.\nEncaminhe os valores separados por vírgula e espaço (', ') para as colunas e com ENTER para novas linhas.\nCaso queira cancelar a operação, utilize o comando /cancel.",)
    return DATA

# Operação de inserção de dados após /update.
async def update_sheet(update:Update, context:ContextTypes.DEFAULT_TYPE):
    message, user = update.message.text, update.message.from_user
    logger.info(f"Usuário {user.first_name} encaminhou os dados {message} para ser inserido na planilha.")
    rows = message.split('\n')
    values = [row.split(', ') for row in rows]
    for row in values : 
        row[-1] = float(row[-1])
        sheet.append_row(row)
    logger.info(f"A inserção dos dados na planilha foi realizada com sucesso.")

# Operação quando o usuário encaminha /cancel para cancelar o /update.        
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info(f"Usuário {user.first_name} cancelou o comando /update.")
    await update.message.reply_html(
        "A inserção de dados na planilha foi cancelada."
    )
    return ConversationHandler.END

def main() :
    TOKEN_BOT = os.getenv('TOKEN_BOT_API')
    
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scopes = scopes)
    
    file = gspread.authorize(credentials)

    # Controle Financeiro = Nome da minha planilha
    workbook = file.open("Controle Financeiro")
    
    global sheet
    sheet = workbook.sheet1

    # Cria a aplicação e devemos passar o token do bot
    app = Application.builder().token(TOKEN_BOT).build()
    
    # Handler = Responsáveis por manusear as mensagens
    
    # Adicionar os comandos (/start; /update_sheet) e qual função será utilizada.
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("update", update_sheet_command)],
        states = {
            DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_sheet)]
        },
        fallbacks=[CommandHandler("cancel", cancel_command)]
    )
    app.add_handler(conv_handler)

    # Tratamento para o que fazer caso o usuário encaminhe algo que seja um texto e não seja um comando
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, non_command))

    # Bot fica rodando até o usuário dar CTRL + C
    app.run_polling()

if __name__ == '__main__':
    main()