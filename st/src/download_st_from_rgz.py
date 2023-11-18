# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, '../ar/src')
import download_from_rgz


def main():
    with open('idp_creds') as f:
        rgz_username = f.readline().strip()
        rgz_password = f.readline().strip()

    cwd = os.getcwd()
    download_path = os.path.join(cwd, 'data/rgz/download')
    if len(os.listdir(download_path)) >= 168:
        print("All files from RGZ already downloaded, skipping download")
        return

    download_from_rgz.download_all_from_rgz(rgz_username, rgz_password, download_path,
                                            entity_type=download_from_rgz.EntityType.ULICE)


if __name__ == '__main__':
    main()
