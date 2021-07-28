import re
import pickle
import os.path
from os import path
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import base64
from datetime import date
import json
import time
from datetime import datetime
user = 'TripACC'
password = 'nm5pfejzbr8dbgk!'

url = 'http://'+user + ':'+ password + '@hive01.northeurope.cloudapp.azure.com:10001/ACC.aspx?ServerID=ACCServer80'

def dlDataFile():

    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    # Using Chrome to access web
    driver = webdriver.Chrome(executable_path="chromedriver\chromedriver.exe", options=chrome_options)#E:\chromedriver_win32\chromedriver.exe
    driver.implicitly_wait(1)
    # Open the website
    driver.get(url)
    # driver.find_element_by_id('didomi-notice-agree-button').click()
    # driver.refresh()
    # driver.find_element_by_xpath("/html/body/main/div/section[1]/div[2]/article/div[1]/div/div[1]/div[4]/div[2]/div[1]/div[2]/div[3]").click()
    # dlBtn = driver.find_element_by_xpath("/html/body/main/div/section[1]/div[2]/article/div[1]/div/div[1]/div[4]/div[2]/div[1]/div[4]/div[4]/div")
    # dlBtn.click()
    element = driver.switch_to.active_element
    print(element)
    element.send_keys(user)
    time.sleep(30000)
    # driver.close()

dlDataFile()
