#librerie
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext  import  Updater, MessageHandler, CommandHandler, CallbackQueryHandler, RegexHandler, Filters, Job
import logging
import datetime
import re
import time
import threading
from threading import Timer

TOKEN = "TOKEN"

#enable logging, sfrutta la libreria per stampare i messaggi e gli errori, in questo caso stampa un messaggio di conferma all'avvio
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)
logging.info('Doing something')

#funzione che manda un  messaggio di benvenuto
def start(bot, update):
    update.message.reply_text('Benvenuto! /info')

#Funzione per l'output degli errori
def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))

#Guida per l'uso dei comandi
def info(bot,update):
	update.message.reply_text('Lista dei comandi:\n/info : Mostra questo menu\n/show : mostra tutti i tuoi  promemoria e appuntamenti\n/appuntamento YYYY-MM-GG/HH:MM : Fissa un nuovo appuntamento\n/memo : Inserisci un nuovo promemoria\n/delmemo : Cancella tutti i tuoi promemoria\n show : mostra tutti i tuoi promemoria e appuntamenti\nAlle 9:00 di ogni giorno MemoBot ti ricorda tutti i tuoi appuntamenti e promemoria')

#Funzione che viene eseguita ogni secondo, controllando nei vari file se ci sono notifiche da inviare a qualche utente
def polling():
	bot = telegram.Bot(token=TOKEN)
	#timestamp attuale
	adesso = time.time()
	#rimuovo le cifre dopo la virgola
	adesso = str(adesso).split('.')[0]

	#notifica gli appuntamenti di cui è giunta l'ora, rimuovendo le entry corrispondenti dal file
	f=open('Appuntamenti.txt', 'r')
	a = f.readlines()
	for x in a:
		m = re.match(r"(\S+) (\S+) (.+)", x)
		data = m.group(1)
		chat = m.group(2)
		nome = m.group(3)
		if data <= adesso:
			ricorda_appuntamento(x, bot)
			a.remove(x)
	f.close()
	f=open("Appuntamenti.txt",'w')
	for x in a:
		f.write("%s" %x)
	f.close()

	i = datetime.datetime.now()
	#si ricordano gli appuntamenti del giorno e tutti i promemoria ogni giorno alle 9:00
	if i.hour == 9 and i.minute == 0 and i.second == 0:
		buongiorno(bot, adesso)

	#Avvio del timer per la prossima operazione di polling
	t = Timer(1.0, polling)
	t.start()

#Data la corrispondente entry nel file Appuntamenti.txt, viene inviata una notifica all'utente per ricordare l'appuntamento
def ricorda_appuntamento(riga, bot):
	m = re.match(r"(\S+) (\S+) (.+)", riga)
	data = m.group(1)
	chat = m.group(2)
	nome = m.group(3)
	data = date(int(data))
	giorno = data.split('/')[0]
	ora = data.split('/')[1]
	stringa = "Ore %s" %ora
	messaggio = "%s - %s" %(stringa, nome)
	bot.sendMessage(chat, messaggio)

#Data la corrispondente entry nel file Appuntamenti.txt, viene inviata una notifica all'utente per ricordare l'appuntamento specificando la data e l'ora
def ricorda_appuntamento_con_data(riga, bot):
	m = re.match(r"(\S+) (\S+) (.+)", riga)
	data = m.group(1)
	chat = m.group(2)
	nome = m.group(3)
	data = date(int(data))
	giorno = data.split('/')[0]
	ora = data.split('/')[1]
	messaggio = "%s(%s): %s" %(giorno,ora, nome)
	bot.sendMessage(chat, messaggio)

#Data la corrispondente entry nel file Promemoria.txt, viene inviata una notifica all'utente per ricordare il promemoria
def ricorda_promemoria(riga, bot):
	m = re.match(r"(\S+) (.+)", riga)
	chat = m.group(1)
	memo = m.group(2)
	stringa = "Promemoria: %s" %memo
	bot.sendMessage(chat, stringa)


#Funzione eseguita quotidianamente, che ricorda a tutti gli utenti gli appuntamenti del giorno e tutti i promemoria
def buongiorno(bot,adesso):
	f=open('Appuntamenti.txt', 'r')
	a=f.readlines()
	for x in a:
		m = re.match(r"(\S+) (\S+) (.+)", x)
		data = m.group(1)
		chat = m.group(2)
		nome = m.group(3)
		t = int(data)-int(adesso)
		data = date(int(data))
		if t < 54000:
			giorno = data.split('/')[0]
			ora = data.split('/')[1]
			stringa = "Ore %s" %ora
			messaggio = "%s - %s" %(stringa, nome)
			bot.sendMessage(chat, messaggio)
	f.close()
	f=open('Promemoria.txt', 'r')
	a=f.readlines()
	for x in a:
		ricorda_promemoria(x,bot)
	f.close()



#Una volta ricevuto il comando di fissare un nuovo appuntamento, viene salvato lo stato della chat in modo da attendere nel prossimo messaggio il nome dell'appuntamento
def ask_date(bot,update,**optional_args):
	query=update.message
	chat_id=query.chat_id
	if len(optional_args['args']) > 0:
		time = timestamp(optional_args['args'][0])
	else:
		time = 0
	if time == 0:
		query.reply_text("Formato data non valido! <YYYY-MM-DD/HH:MM>")
		return
	f=open('Stati.txt', 'r')
	a=f.readlines()
	flag = 0
	for x in a:
		m = re.match(r"(\S+) (\S+) (\S+)", x)
		chat = m.group(1)
		stato = m.group(2)
		data = m.group(3)
		if chat == str(chat_id):
			a.remove(x)
			a.append("%s %s %d " %(chat,"1", time))
			flag = 1
	f.close
	if flag == 0:
		f=open("Stati.txt",'a')
		f.write("%s %s %d \n" %(chat_id, "1", time))
	else:
		f=open("Stati.txt",'w')
		for x in a:
			f.write("%s\n" %x)
	f.close
	query.reply_text("Inserisci il nome dell'appuntamento")

#Una volta ricevuto il comando di salvare un nuovo promemoria, viene salvato lo stato della chat in modo da attendere nel prossimo messaggio il contenuto del memo
def ask_memo(bot,update):
	query=update.message
	chat_id=query.chat_id
	f=open('Stati.txt', 'r')
	a=f.readlines()
	flag = 0
	for x in a:
		m = re.match(r"(\S+) (\S+) (\S+)", x)
		chat = m.group(1)
		stato = m.group(2)
		data = m.group(3)
		if chat==str(chat_id):
			a.remove(x)
			a.append("%s %s %s " %(chat,"2", "0"))
			flag = 1
	f.close
	if flag == 0:
		f=open("Stati.txt",'a')
		f.write("%s %s %s \n" %(chat_id, "2", "0"))
	else:
		f=open("Stati.txt",'w')
		for x in a:
			f.write("%s\n" %x)
	f.close
	query.reply_text("Inserisci il promemoria")

#ogni volta che viene ricevuto un messaggio di testo (non comando) viene controllato lo stato della chat del mittente e si sceglie come agire
def controlla_stato(bot,update):
	query = update.message
	chat_id = query.chat_id
	f=open('Stati.txt', 'r')
	a=f.readlines()
	flag = 0
	stato = 0
	for x in a:
		m = re.match(r"(\S+) (\S+) (\S+)", x) #funziona
		chat = m.group(1)
		statot = m.group(2)
		data = m.group(3)
		if chat == str(chat_id):
			stato = statot
			opt_data = data
			a.remove(x)
	f.close
	f=open('Stati.txt', 'w')
	for  x in a:
		f.write("%s \n" %x)
	if stato == "1": #Attesa del nome di un'Appuntamento
		salva_appuntamento(query.text,query.chat_id, opt_data)
		bot.sendMessage(chat_id,"Appuntamento salvato!")
	if stato == "2": #Attendo il testo di un promemoria
		salva_memo(query.text, query.chat_id)
		bot.sendMessage(chat_id,"Promemoria salvato!")

	if stato == 0: #Stato iniziale
		bot.sendMessage(chat_id, "Messaggio non valido /info")

#Inserimento di una nuova entry nel file Appuntamenti.txt
def salva_appuntamento (nome,chat, data):
	print("Salvo appuntamento\n")
	flag = 0
	f=open('Appuntamenti.txt', 'r')
	stringa = "%s %s %s\n" %(data, chat,nome)
	a = f.readlines()
	for i in range(len(a)):
		if flag == 0:
			m = re.match(r"(\S+) (\S+) (.+)", a[i])
			datat = m.group(1)
			if datat >= data:
				a.insert(i,stringa)
				flag = 1
	f.close()
	if flag == 0:
		a.append("%s" %stringa)
	f=open("Appuntamenti.txt",'w')
	for x in a:
		f.write("%s" %x)
	f.close()

#Inserimento di un nuovo promemoria nel file Promemoria.txt
def salva_memo(memo,chat_id):
	print("Salvo promemoria\n")
	flag = 0
	f=open('Promemoria.txt', 'r')
	stringa = "%s %s\n" %(chat_id,memo)
	a = f.readlines()
	for i in range(len(a)):
		if flag == 0:
			m = re.match(r"(\S+) (.+)", a[i])
			chat = m.group(1)
			memo = m.group(2)
			if int(chat) >= chat_id:
				flag = 1
				a.insert(i,stringa)
	f.close()
	if flag == 0:
		a.append("%s" %stringa)
	f=open("Promemoria.txt",'w')
	for x in a:
		f.write("%s" %x)
	f.close()

#Data una stringa contenente una data nel formato YYYY-MM-DD/HH:MM, restituisce il corrispondente timestamp
def timestamp(data):
	m = re.match(r"(\d\d\d\d)-(\d\d)-(\d\d)/(\d\d):(\d\d)", data)
	if m:
		anno = m.group(1)
		mese = m.group(2)
		giorno = m.group(3)
		#ts = time.time() timestamp attuale con sensibilità sotto il secondo
		timestamp = time.mktime(datetime.datetime.strptime(data, "%Y-%m-%d/%H:%M").timetuple())
		ts = str(timestamp).split('.')[0]
		return int(ts)
	else:
		return 0

#Dato un timestamp, restituisce la data corrispondente nel formato Y-M-D/H:M:S
def date(timestamp):
	return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d/%H:%M:%S')

#elimina tutti i promemoria dell'utente che ne fa richiesta
def delete_memo(bot, update):
	query = update.message
	chat_id = query.chat_id
	f=open('Promemoria.txt', 'r')
	a = f.readlines()
	b=[]
	for i in range(len(a)):
		m = re.match(r"(\S+) (.+)", a[i])
		chat = m.group(1)
		memo = m.group(2)
		chat=int(chat)
		if chat != chat_id:
			b.append(a[i])
	f.close()
	f=open("Promemoria.txt",'w')
	for x in b:
		f.write("%s" %x)
	f.close()
	update.message.reply_text("Promemoria eliminati!")

#mostra gli appuntamenti e i promemoria dell'utente che ne fa richiesta
def show(bot,update):
	query = update.message
	chat_id = query.chat_id
	f=open('Appuntamenti.txt', 'r')
	a = f.readlines()
	flag = 0
	for x in a:
		m = re.match(r"(\S+) (\S+) (.+)", x)
		data = m.group(1)
		chat = m.group(2)
		nome = m.group(3)
		if int(chat) == chat_id:
			if flag == 0:
				bot.sendMessage(chat_id, "Appuntamenti:")
				flag = 1
			ricorda_appuntamento_con_data(x, bot)
	f.close()
	f=open('Promemoria.txt', 'r')
	a = f.readlines()
	flag = 0
	for x in a:
		m = re.match(r"(\S+) (.+)", x)
		chat = m.group(1)
		memo = m.group(2)
		if int(chat) == chat_id:
			ricorda_promemoria(x, bot)
	f.close()

def main():
	#inizializza l'oggetto updater sul nostro bot, di cui indichiamo il token, l'updater ha il compito di rilevare aggiornamenti dai server di telegram riguardanti messaggi inviati al bot
	updater = Updater(TOKEN)
	#inizializza l'oggetto dispatcher, che raccoglie gli aggiornamenti colti dall'updater e li gira a diversi handler in base al loro contenuto
	dp=updater.dispatcher
	dp.add_handler(CommandHandler('appuntamento',ask_date, pass_args=True))
	dp.add_handler(CommandHandler('memo',ask_memo))
	dp.add_handler(CommandHandler('start',start))
	dp.add_handler(CommandHandler('info',info))
	dp.add_handler(CommandHandler('delmemo',delete_memo))
	dp.add_handler(CommandHandler('show',show))
	dp.add_handler(MessageHandler(Filters.text,controlla_stato))

	# log all errors
	dp.add_error_handler(error)

	#avvia polling del bot
	updater.start_polling()

	#Avvio del primo timer per il polling
	t = Timer(1.0, polling)
	t.start()

	#esegue "updater.stop()" quando si usa ctrl+C
	updater.idle()

if __name__ == '__main__':
	main()
