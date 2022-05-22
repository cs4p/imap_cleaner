# imap_cleaner

Simple Python script that will connect to an imap server and move messages from your inbox into specific folders. It does this by scanning the target folder and moving any messages from the same email address into the folder

## Usage

1. clone the repo and install requirements
2. create a file, config.py, set the following values:
   1. imap_user = "your_user_id" 
   2. imap_password = "your_imap_password"
   3. imap_server = "your_imap_server"
   4. folder_list_order = python list of folders in priority order.  This is used only for the clean up function.
3. run `python imap_cleaner.py`