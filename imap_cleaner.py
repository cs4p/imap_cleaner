import datetime
import logging
import os.path
import sys
import time
from environs import Env
from imapclient import IMAPClient
import sqlite3

env = Env()
env.read_env()  # read .env file, if it exists
BASE_DIR = os.path.curdir
db_file_name='mailcleaner.db'

imap_server = env("IMAP_SERVER", "imap.fastmail.com")
imap_user = env("IMAP_USER")
imap_password = env("IMAP_PASSWORD")
MINUTES_BETWEEN_UPDATES = int(env("MINUTES_BETWEEN_UPDATES"))


def server_login(mail_server, mail_user, mail_password):
    server = IMAPClient(mail_server, use_uid=True)
    server.login(mail_user, mail_password)
    return server


def init_db(db_file_name='mailcleaner.db'):
    conn_db = sqlite3.connect(os.path.join(BASE_DIR, db_file_name))
    conn_db.execute('''CREATE TABLE IF NOT EXISTS mailcleaner (
    ID            INTEGER  not null primary key autoincrement,
    email_address TEXT not null,
    folder        INT  not null,
    DTS           TIMESTAMP)''')
    conn_db.row_factory = lambda cursor, row: row[0]
    cur = conn_db.execute('SELECT MAX(DTS) from mailcleaner;')
    max_DTS = cur.fetchone()
    if max_DTS is None:
        update_database(conn_db)
    else:
        max_DTS_datetime_object = datetime.datetime.strptime(max_DTS, '%Y-%m-%d %H:%M:%S.%f')
        time_since_last_update = datetime.datetime.now() - max_DTS_datetime_object
        minutes_since_last_update = int(time_since_last_update.total_seconds() / 60)
        if minutes_since_last_update > MINUTES_BETWEEN_UPDATES:
            update_database(conn_db)
    return conn_db


def move_email(server, msg, dst_folder):
    if not server.folder_exists(dst_folder):
        server.create_folder(dst_folder)
    server.move(msg, dst_folder)


def add_or_update_email(email_addr, folder_name, conn_db, DTS):
    sql = "select email_address from mailcleaner where email_address = ?"
    cur = conn_db.execute(sql, (email_addr,)).fetchall()
    if len(cur) == 0:
        conn_db.execute("INSERT INTO mailcleaner (email_address, folder, DTS) VALUES(?,?,?)", (email_addr, folder_name, DTS))
        conn_db.commit()
    else:
        conn_db.execute("UPDATE mailcleaner set folder = ?, DTS= ? where email_address = ?", (folder_name, DTS, email_addr))
        conn_db.commit()


def update_email_list_for_folder(server, folder_name, conn_db):
    logging.info('Getting email list for folder ' + folder_name)
    server.select_folder(folder_name)
    # TODO: Add filter here for last date
    messages = server.search()
    DTS = datetime.datetime.now()
    for msgid, data in server.fetch(messages, ['ENVELOPE']).items():
        envelope = data[b'ENVELOPE']
        if envelope.from_ is not None:
            for addr in envelope.from_:
                email_addr = '@'.join([str(addr.mailbox.decode()), str(addr.host.decode())]);
                logging.debug('Add or update email address %s' % email_addr)
                add_or_update_email(email_addr, folder_name, conn_db, DTS)


def get_email_list_for_folder(folder_name, conn_db):
    sql = "select email_address from mailcleaner where folder = ?"
    email_filter_list = conn_db.execute(sql, (folder_name,)).fetchall()
    return email_filter_list


def apply_folder_filters(server, messages, email_list, folder_name):
    counter = 0
    for msgid, data in server.fetch(messages, ['ENVELOPE']).items():
        envelope = data[b'ENVELOPE']
        for addr in envelope.from_:
            email_addr = '@'.join([str(addr.mailbox.decode()), str(addr.host.decode())])
            if email_addr in email_list:
                server.move(msgid, folder_name)
                counter = counter + 1
    return counter


def sort_mail(conn_db):
    start_logging()
    logging.info('###################################################################################################')
    logging.info('Starting operation...')
    server = server_login(imap_server, imap_user, imap_password)
    select_info = server.select_folder('INBOX')
    logging.info('%d messages in INBOX' % select_info[b'EXISTS'])
    folder_list = server.list_folders('Categories/')
    for fldr in folder_list:
        folder_name = fldr[2]
        new_messages = server.search()
        email_list = get_email_list_for_folder(folder_name, conn_db)
        server.select_folder('INBOX')
        logging.info('Looking for new messages to move to ' + folder_name)
        p = apply_folder_filters(server, new_messages, email_list, folder_name)
        logging.info(' '.join(['Moved', str(p), 'messages to', folder_name]))
        select_info = server.select_folder('INBOX')
        logging.info('%d messages in INBOX' % select_info[b'EXISTS'])
    logging.info('Finished moving messages. %d messages remain in INBOX' % select_info[b'EXISTS'])
    server.logout()


def clean_mail():
    """ Sorts all old mail into the currently defined folder in the database"""
    start_logging()
    conn_db = init_db()
    logging.info('###################################################################################################')
    logging.info('Starting email cleanup...')
    server = server_login(imap_server, imap_user, imap_password)
    folder_list = server.list_folders('Categories/')
    for fldr in folder_list:
        folder_name = fldr[2]
        select_info = server.select_folder(folder_name)
        existing_messages = server.search()
        for msgid, data in server.fetch(existing_messages, ['ENVELOPE']).items():
            envelope = data[b'ENVELOPE']
            for addr in envelope.from_:
                email_addr = '@'.join([str(addr.mailbox.decode()), str(addr.host.decode())])
                sql = "select folder from mailcleaner where email_address = ?"
                email_folder = conn_db.execute(sql, (email_addr,)).fetchone()
                if email_folder != folder_name:
                    logging.info(' '.join(['Moved message from ', str(email_addr), ' from folder ',email_folder, ' to folder ', folder_name]))
                    server.move(msgid, email_folder)
    server.logout()

def update_database(conn_db):
    start_logging()
    logging.info('###################################################################################################')
    logging.info('Starting operation, update database only...')
    server = server_login(imap_server, imap_user, imap_password)
    select_info = server.select_folder('INBOX')
    logging.info('%d messages in INBOX' % select_info[b'EXISTS'])
    folder_list = server.list_folders('Categories/')
    for fldr in folder_list:
        folder_name = fldr[2]
        new_messages = server.search()
        update_email_list_for_folder(server, folder_name, conn_db)


def start_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
        handlers=[
            logging.FileHandler('imap_cleaner.log'),
            logging.StreamHandler()]
    )


def main(p=False):
    conn_db = init_db()
    sort_mail(conn_db)
    conn_db.close()
    if p:
        logging.info("running in persistent mode, sleeping for 300 seconds")
        time.sleep(300)
        main(True)


if __name__ == '__main__':
    p = False
    if len(sys.argv) > 1:
        p = sys.argv[1]
    sys.exit(main(p))

