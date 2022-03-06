# imap_cleaner

Simple Python script that will connect to an imap server and move messages from your inbox into specific folders. It does this by scanning the target folder and moving any messages from the same email address into the folder

To run the docker container and have the files output to the local directory:

docker run -d --mount type=bind,source="$(pwd)",target=/usr/src/app  image_name
