import json
import logging
from datetime import time
from sievelib.factory import FiltersSet
from imap_cleaner import server_login, imap_server, imap_user, imap_password, get_email_list_for_folder, apply_folder_filters, folder_list_order

# NOTE: none of this works :)

def add_rule_to_filter_set(email_list, dest, rule_name, filter_set):
    criteria = []
    for e in email_list:
        c = ("Sender", ":is", e)
        criteria.append(c)
    filter_set.addfilter(rule_name, criteria, [("fileinto", dest), ])


def create_fastmail_rule(email_list, rule_name, ):
    search_string = " OR from:".join(email_list)
    search_string = "from:" + search_string
    time_stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime())

    rule_config = dict(
        name=rule_name, combinator="any", conditions="null", search=search_string, markRead="false",
        markFlagged="false", showNotification="false", redirectTo="null", fileIn="dest",
        skipInbox="true", snoozeUntil="null", discard="false", markSpam="false", stop="false",
        created=time_stamp, updated=time_stamp, previousFileInName="null"
        )
    r = json.dumps(rule_config)
    return r


def clean_up_folder(target_folder):
    # logging.basicConfig(
    #     level=logging.INFO,
    #     format='%(levelname)s: %(asctime)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
    #     handlers=[logging.FileHandler('imap_cleaner.log'), logging.StreamHandler()]
    #     )
    logging.info('###################################################################################################')
    logging.info('Starting folder clean up...')
    server = server_login(imap_server, imap_user, imap_password)
    email_list = get_email_list_for_folder(server, target_folder)
    folder_list = server.list_folders('Categories/')
    for fldr in folder_list:
        folder_name = fldr[2]
        if folder_name != target_folder:
            server.select_folder(folder_name)
            new_messages = server.search()
            p = apply_folder_filters(server, new_messages, email_list, folder_name)
            logging.info(' '.join(['Moved', str(p), 'messages from', folder_name, "to", target_folder]))
    server.logout()
    logging.info('Finished moving messages.')


def clean_all_folders():
    for target_folder in folder_list_order:
        clean_up_folder(target_folder)


def create_mail_rules():
    # logging.basicConfig(
    #     level=logging.INFO,
    #     format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
    #     handlers=[logging.FileHandler('imap_cleaner.log'), logging.StreamHandler()]
    #     )
    logging.info('###################################################################################################')
    logging.info('Starting operation...')
    server = server_login(imap_server, imap_user, imap_password)
    folder_list = server.list_folders('Categories/')
    filter_set = FiltersSet("Rules")
    fastmail_rules = []
    for fldr in folder_list:
        folder_name = fldr[2]
        email_list = get_email_list_for_folder(server, folder_name)
        logging.info('Adding a rule to filter set')
        add_rule_to_filter_set(email_list, folder_name, folder_name, filter_set)
        fastmail_rules.append(create_fastmail_rule(email_list, folder_name, folder_name))
    logging.info('outputting filter set')
    rules_file = open('rules.sieve', 'w')
    rules_file.write(str(filter_set.__str__()))
    rules_file.close()
    logging.info('outputting fastmail rules')
    fastmail_rules_string = "[" + ",".join(fastmail_rules) + "]"
    rules_file = open('mailrules.json', 'w')
    rules_file.write(fastmail_rules_string)
    rules_file.close()