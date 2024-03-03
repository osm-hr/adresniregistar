# -*- coding: utf-8 -*-

import json
import os
import time
from enum import Enum

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumwire import webdriver

from common import OPSTINE_TO_SKIP, normalize_name

SLEEP_TIME = 2


class EntityType(Enum):
    ULICE = 1
    KUCNI_BROJEVI = 2


class DataFormat(Enum):
    CSV = 1
    SHAPEFILE = 2


def login(driver, rgz_username, rgz_password):
    driver.get("https://download.geosrbija.rs/download/")

    time.sleep(SLEEP_TIME)
    driver.find_element(By.CSS_SELECTOR, "div.actions > button.btn-rgz").click()

    time.sleep(SLEEP_TIME)
    driver.find_element(By.CSS_SELECTOR, "input#username").send_keys(rgz_username)
    driver.find_element(By.CSS_SELECTOR, "input#password").send_keys(rgz_password)
    driver.find_element(By.CSS_SELECTOR, "input#kc-login").click()

    time.sleep(SLEEP_TIME * 3)
    try:
        driver.find_element(By.CSS_SELECTOR, "footer.shepherd-footer > button.red").click()
    except NoSuchElementException:
        pass


def click_novo_preuzimanje(driver):
    retries = 0
    while True:
        try:
            time.sleep(SLEEP_TIME * 3)
            driver.find_element(By.CSS_SELECTOR, "button#newDownloadButton").click()
            time.sleep(SLEEP_TIME)
            break
        except ElementClickInterceptedException as e:
            retries += 1
            if retries == 3:
                raise e


def select_opstina(driver, opstina_name):
    time.sleep(SLEEP_TIME)
    opstina = driver.find_elements(By.CSS_SELECTOR, 'p-dropdown.p-inputwrapper')[0]
    opstina.click()

    opstina.find_element(By.CSS_SELECTOR, 'input.p-component').clear()
    opstina.find_element(By.CSS_SELECTOR, 'input.p-component').send_keys(opstina_name)
    counter = 0
    while True:
        counter += 1
        if counter > 100:
            # This is too much iterations...
            raise Exception("Cannot select opstina")

        opstina.find_element(By.CSS_SELECTOR, 'input.p-component').send_keys(Keys.DOWN)
        time.sleep(SLEEP_TIME)
        if opstina.find_element(By.CSS_SELECTOR, 'span').text in opstina_name:
            opstina.find_element(By.CSS_SELECTOR, 'input.p-component').send_keys(Keys.ENTER)
            break

    time.sleep(SLEEP_TIME)


def select_data_format(driver, text="Shape"):
    retries = 0
    while True:
        try:
            time.sleep(SLEEP_TIME)
            text_element = driver.find_elements(By.CSS_SELECTOR, 'p-dropdown.p-inputwrapper')[2]
            text_element.click()
            time.sleep(SLEEP_TIME)
            text_element.find_element(By.CSS_SELECTOR, 'input.p-component').clear()
            text_element.find_element(By.CSS_SELECTOR, 'input.p-component').send_keys(text + Keys.DOWN + Keys.ENTER)
            break
        except NoSuchElementException as e:
            retries += 1
            if retries == 3:
                raise e


def select_kucni_broj(driver):
    driver.find_element(By.CSS_SELECTOR, 'li[aria-label="Adresni registar"]').click()
    time.sleep(SLEEP_TIME)
    driver.find_element(By.CSS_SELECTOR, 'li[aria-label="Kućni broj"]').click()
    time.sleep(SLEEP_TIME)


def download_all_from_rgz(rgz_username, rgz_password, download_path,
                          entity_type=EntityType.KUCNI_BROJEVI, dataFormat = DataFormat.CSV):
    profile = webdriver.FirefoxOptions()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", download_path)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")

    service = Service(executable_path='./geckodriver')
    driver = webdriver.Firefox(options=profile, service=service)
    driver.implicitly_wait(10)

    login(driver, rgz_username, rgz_password)

    time.sleep(SLEEP_TIME * 3)
    x_tour = driver.find_element(By.CSS_SELECTOR, "button.shepherd-cancel-icon")
    if x_tour:
        x_tour.click()
        time.sleep(SLEEP_TIME)

    click_novo_preuzimanje(driver)
    if entity_type == EntityType.KUCNI_BROJEVI:
        select_kucni_broj(driver)

    all_opstine = []
    for request in driver.requests:
        if request.url == "https://download.geosrbija.rs/download-api/backend/opstine":
            opstine_str = request.response.body.decode("utf-8")
            all_opstine = json.loads(opstine_str)
            break
    if len(all_opstine) == 0:
        raise Exception("Cannot fetch all opstine, quitting")

    total_downloaded = 0
    for i, opstina in enumerate(all_opstine):
        opstina_name = opstina["opstinaImel"]
        print(f'{i}/{len(all_opstine)} Processing {opstina_name}')
        if os.path.exists(os.path.join(download_path, normalize_name(opstina_name) + '.zip')):
            print(f'Skipping opstina {opstina_name}, already exist')
            continue
        if opstina_name in OPSTINE_TO_SKIP:
            print(f'Skipping opstina {opstina_name}, Kosovo is not in RGZ')
            continue

        select_opstina(driver, opstina_name)
        driver.find_element(By.CSS_SELECTOR, 'input.p-inputtext[placeholder="Naziv fajla"]').clear()
        driver.find_element(By.CSS_SELECTOR, 'input.p-inputtext[placeholder="Naziv fajla"]').send_keys(normalize_name(opstina_name))

        if dataFormat == DataFormat.SHAPEFILE:
            select_data_format(driver, "Shape")

        time.sleep(SLEEP_TIME)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(SLEEP_TIME * 5)
        total_downloaded += 1
        if total_downloaded > 10:
            driver.refresh()
            time.sleep(SLEEP_TIME * 10)
            click_novo_preuzimanje(driver)
            if entity_type == EntityType.KUCNI_BROJEVI:
                select_kucni_broj(driver)
            total_downloaded = 0
    driver.quit()


def main():
    if not os.path.exists('idp_creds'):
        print("Before running download, you need to create file named 'idp_creds' with two lines.")
        print("First line should contain username to log in to https://download-tmp.geosrbija.rs/download/")
        print("Second line should contain password to log in to https://download-tmp.geosrbija.rs/download/")
        return

    with open('idp_creds') as f:
        rgz_username = f.readline().strip()
        rgz_password = f.readline().strip()

    cwd = os.getcwd()
    download_path = os.path.join(cwd, 'data/rgz/download')
    if len(os.listdir(download_path)) >= 168:
        print("All files from RGZ already downloaded, skipping download")
        return

    download_all_from_rgz(rgz_username, rgz_password, download_path)


if __name__ == '__main__':
    main()
