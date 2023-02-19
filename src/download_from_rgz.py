# -*- coding: utf-8 -*-

import json
import os
import time

from selenium import webdriver
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from seleniumwire import webdriver

SLEEP_TIME = 1
OPSTINE_TO_SKIP = ['VITINA', 'VUČITRN', 'GLOGOVAC', 'GNJILANE', 'GORA', 'DEČANI', 'ĐAKOVICA',
                   'ZVEČAN', 'ZUBIN POTOK', 'ISTOK', 'KAČANIK', 'KLINA', 'KOSOVSKA MITROVICA',
                   'KOSOVO POLJE', 'KOSOVSKA KAMENICA', 'LEPOSAVIĆ', 'LIPLJAN', 'NOVO BRDO',
                   'OBILIĆ', 'ORAHOVAC', 'PEĆ', 'PODUJEVO', 'PRIŠTINA', 'PRIZREN', 'SRBICA',
                   'SUVA REKA', 'UROŠEVAC', 'ŠTIMLJE', 'ŠTRPCE']


def login(driver, rgz_username, rgz_password):
    driver.get("https://download-tmp.geosrbija.rs/download/")

    time.sleep(SLEEP_TIME)
    driver.find_element(By.CSS_SELECTOR, "button.p-ripple").click()

    time.sleep(SLEEP_TIME)
    driver.find_element(By.CSS_SELECTOR, "input#username").send_keys(rgz_username)
    driver.find_element(By.CSS_SELECTOR, "input#password").send_keys(rgz_password)
    driver.find_element(By.CSS_SELECTOR, "input#kc-login").click()


def click_novo_preuzimanje(driver):
    retries = 0
    while True:
        try:
            time.sleep(SLEEP_TIME * 3)
            driver.find_element(By.CSS_SELECTOR, "button.btn1").click()
            time.sleep(SLEEP_TIME)
            break
        except ElementClickInterceptedException as e:
            retries += 1
            if retries == 3:
                raise e


def select_kucni_broj(driver):
    driver.find_element(By.CSS_SELECTOR, 'li[aria-label="Adresni registar"]').click()
    time.sleep(SLEEP_TIME)
    driver.find_element(By.CSS_SELECTOR, 'li[aria-label="Kućni broj"]').click()
    time.sleep(SLEEP_TIME)


def download_all_from_rgz(rgz_username, rgz_password, download_path):
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", download_path)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")

    driver = webdriver.Firefox(firefox_profile=profile)
    driver.implicitly_wait(10)

    login(driver, rgz_username, rgz_password)
    click_novo_preuzimanje(driver)
    select_kucni_broj(driver)

    all_opstine = []
    for request in driver.requests:
        if request.url == "https://download-tmp.geosrbija.rs/download-api/backend/opstine":
            opstine_str = request.response.body.decode("utf-8")
            all_opstine = json.loads(opstine_str)
            break
    if len(all_opstine) == 0:
        raise Exception("Cannot fetch all opstine, quitting")

    total_downloaded = 0
    for i, opstina in enumerate(all_opstine):
        opstina_name = opstina["opstinaImel"]
        print(f'{i}/{len(all_opstine)} Processing {opstina_name}')
        if os.path.exists(os.path.join(download_path, opstina_name + '.zip')):
            print(f'Skipping opstina {opstina_name}, already exist')
            continue
        if opstina_name in OPSTINE_TO_SKIP:
            print(f'Skipping opstina {opstina_name}, Kosovo is not in RGZ')
            continue

        time.sleep(SLEEP_TIME)
        opstina = driver.find_elements(By.CSS_SELECTOR, 'p-dropdown.p-inputwrapper')[0]
        opstina.click()
        time.sleep(SLEEP_TIME)
        opstina.find_element(By.CSS_SELECTOR, 'input.p-component').clear()
        opstina.find_element(By.CSS_SELECTOR, 'input.p-component').send_keys(opstina_name + Keys.DOWN + Keys.ENTER)
        time.sleep(SLEEP_TIME)
        driver.find_element(By.CSS_SELECTOR, 'input.p-inputtext[placeholder="Naziv fajla"]').clear()
        driver.find_element(By.CSS_SELECTOR, 'input.p-inputtext[placeholder="Naziv fajla"]').send_keys(opstina_name)
        time.sleep(SLEEP_TIME)
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(SLEEP_TIME * 5)
        total_downloaded += 1
        if total_downloaded > 10:
            driver.refresh()
            time.sleep(SLEEP_TIME * 10)
            click_novo_preuzimanje(driver)
            select_kucni_broj(driver)
            total_downloaded = 0
    os.remove(os.path.join(download_path, 'UB.zip'))
    os.remove(os.path.join(download_path, 'TOPOLA.zip'))
    os.remove(os.path.join(download_path, 'RAČA.zip'))
    print("Download UB, TOPOLA and RAČA manually")
    driver.quit()


def main():
    if not os.path.exists('rgz_creds'):
        print("Before runnning download, you need to create file named 'rgz_cred' with two lines.")
        print("First line should contain username to log in to RGZ")
        print("Second line should contain password to log in to RGZ")
        return

    with open('rgz_creds') as f:
        rgz_username = f.readline().strip()
        rgz_password = f.readline().strip()

    cwd = os.getcwd()
    download_path = os.path.join(cwd, 'data/rgz_opstine/download')
    download_all_from_rgz(rgz_username, rgz_password, download_path)




if __name__ == '__main__':
    main()