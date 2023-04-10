import \
    sys

import semver
import os

BASEDIR = os.path.curdir
VERSION_FILE = os.path.join(BASEDIR, 'version.txt')


def get_version():
    if os.path.exists(VERSION_FILE):
        vf = open(VERSION_FILE,'r')
        current_version = semver.Version.parse(vf.readline())
    else:
        vf = open(VERSION_FILE,'w')
        current_version = semver.Version.parse('0.0.0')
        vf.write(current_version)
    vf.close()
    return current_version


def update_version_file(new_version):
    vf = open(VERSION_FILE,'w')
    vf.write(str(new_version.finalize_version()))
    vf.close()


def patch():
    current_version = get_version()
    new_version = current_version.bump_patch()
    update_version_file(new_version)
    return new_version


def main():
    new_version = patch()
    cmd = ('docker buildx build --platform linux/amd64,linux/arm64 --push -t cs4p/imap_cleaner:%s .' % new_version)
    output = os.popen(cmd).read()
    print(output)

if __name__ == '__main__':
    sys.exit(main())