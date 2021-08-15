import time, json, logging

from imapclient import IMAPClient
from sievelib.factory import FiltersSet

from config import imap_server, imap_user, imap_password, folder_list

def server_login(imap_server, imap_user, imap_password):
    server = IMAPClient(imap_server, use_uid=True)
    server.login(imap_user, imap_password)
    return server





def move_email(server, msg, dst_folder):
    if not server.folder_exists(dst_folder):
        server.create_folder(dst_folder)
    server.move(msg, dst_folder)


def get_folder_filter(server, folder_name):
    logging.info('Getting email list for folder ' + folder_name)
    server.select_folder(folder_name)
    messages = server.search()
    email_filter_list = []
    for msgid, data in server.fetch(messages, ['ENVELOPE']).items():
        envelope = data[b'ENVELOPE']
        for addr in envelope.from_:
            email_addr = '@'.join([str(addr.mailbox.decode()),str(addr.host.decode())])
            if email_addr not in email_filter_list:
                email_filter_list.append(email_addr)
    logging.info(' '.join(['Found', str(len(email_filter_list)), 'email addresses for', folder_name]))

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

def AddRuleToFilterSet(email_list, dest, rule_name,filter_set):
    criteria = []
    for e in email_list:
        c = ("Sender", ":is", e)
        criteria.append(c)
    filter_set.addfilter(rule_name, criteria, [("fileinto", dest), ])
    # return filter_set.tosieve()

def createFastmailRule(email_list, dest, rule_name,):
    search_string = " OR from:".join(email_list)
    search_string = "from:" + search_string
    time_stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.localtime())

    rule_config = dict(name=rule_name, combinator="any", conditions="null", search=search_string, markRead="false",
                       markFlagged="false", showNotification="false", redirectTo="null", fileIn="dest",
                       skipInbox="true", snoozeUntil="null", discard="false", markSpam="false", stop="false",
                       created=time_stamp, updated=time_stamp, previousFileInName="null")
    r = json.dumps(rule_config)
    return r



def run():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.FileHandler('imap_cleaner.log'), logging.StreamHandler()])
    logging.info('###################################################################################################')
    logging.info('Starting operation...')
    server = server_login(imap_server, imap_user, imap_password)
    select_info = server.select_folder('INBOX')
    logging.info('%d messages in INBOX' % select_info[b'EXISTS'])
    folder_list = server.list_folders('Categories/')
    filter_set = FiltersSet("Rules")
    fastmailRules = []
    for fldr in folder_list:
        folder_name = fldr[2]
        email_list = []
        new_messages = server.search()
        email_list = get_folder_filter(server, folder_name)
        logging.info('Adding a rule to filter set')
        AddRuleToFilterSet(email_list,folder_name,folder_name,filter_set)
        fastmailRules.append(createFastmailRule(email_list,folder_name,folder_name))
        select_info = server.select_folder('INBOX')
        logging.info('Looking for new messages to move to ' + folder_name)
        p = apply_folder_filters(server, new_messages, email_list, folder_name)
        logging.info(' '.join(['Moved', str(p), 'messages to', folder_name]))
        select_info = server.select_folder('INBOX')
        logging.info('%d messages in INBOX' % select_info[b'EXISTS'])
    logging.info('Finished moving messages. %d messages remain in INBOX' % select_info[b'EXISTS'])
    logging.info('outputting filter set')
    rules_file = open('rules.sieve','w')
    rules_file.write(str(filter_set.__str__()))
    rules_file.close()
    logging.info('outputting fastmail rules')
    fastmail_rules_string = "[" + ",".join(fastmailRules) + "]"
    rules_file = open('mailrules.json', 'w')
    rules_file.write(fastmail_rules_string)
    rules_file.close()
    server.logout()