from imapclient import IMAPClient
from config import imap_server,imap_user,imap_password


def server_login(imap_server,imap_user,imap_password):
    server = IMAPClient(imap_server, use_uid=True)
    server.login(imap_user, imap_password)
    return server

def move_email(server,msg,dst_folder):
    if not server.folder_exists(dst_folder):
        server.create_folder(dst_folder)
    server.move(msg,dst_folder)

def get_folder_filter(server,folder_name):
    server.select_folder(folder_name)
    messages = server.search()
    email_filter_list = []
    for msgid, data in server.fetch(messages, ['ENVELOPE']).items():
        envelope = data[b'ENVELOPE']
        for addr in envelope.sender:
            if addr not in email_filter_list:
                email_filter_list.append(str(addr))
    return email_filter_list

def apply_folder_filters(server, messages, email_list, folder_name):
    counter = 0
    for msgid, data in server.fetch(messages, ['ENVELOPE']).items():
        envelope = data[b'ENVELOPE']
        for addr in envelope.sender:
            if str(addr) in email_list:
                server.move(msgid,folder_name)
                counter = counter + 1
    return counter

def run():
    server = server_login(imap_server,imap_user, imap_password)
    select_info = server.select_folder('INBOX')
    print('%d messages in INBOX' % select_info[b'EXISTS'])
    print('Processing...')
    folder_list = ['vendor','Spam','unsubscribe','social_media','Family','school']
    for fldr in folder_list:
        email_list = []
        new_messages = server.search()
        email_list = get_folder_filter(server, fldr)
        select_info = server.select_folder('INBOX')
        p = apply_folder_filters(server, new_messages, email_list, fldr)
        print(' '.join(['Moved',str(p),'messages to',fldr]))
        print('%d messages in INBOX' % select_info[b'EXISTS'])

    print('%d messages in INBOX' % select_info[b'EXISTS'])
    server.logout()
