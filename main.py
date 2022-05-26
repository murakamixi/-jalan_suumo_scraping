from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import requests
from bs4 import BeautifulSoup

from selenium.common.exceptions import NoSuchElementException

from PIL import Image
import io

import time

import pandas as pd

import utils.functions as F
import utils.data as data

from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS
flags.DEFINE_string('pref_name', 'Yamagata', 'pref name')
flags.DEFINE_string('target', 'suumo', 'suumo or jalan')

def suumo():
  house_id = 0
  pref_sum_count = 0

  for url in [data.urls[FLAGS.pref_name]]:
      prefecture_name = FLAGS.pref_name
      pref_sum_count += 1
      url = url
      data_list = []
      page_count = 0

      logging.info(pref_sum_count, prefecture_name)

      options = Options()
      options.add_argument('--headless')
      browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)
      browser.get(url)

      url = browser.current_url
      res = requests.get(url)
      soup = BeautifulSoup(res.content, 'html.parser')
      a_elems = soup.find_all('div', attrs={'class' : 'property_unit-header'})

      options = Options()
      options.add_argument('--headless')
      browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)
      browser.get(url)

			# 次へをクリックして、ページがなくなるまで繰り返しページを探索する
      while True:
          url = browser.current_url
          logging.info(url)
          #ブラウザの起動
          options = Options()
          options.add_argument('--headless')
          browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)

          browser.get(url)

          try:
              res = requests.get(url)
              soup = BeautifulSoup(res.content, 'html.parser')
              urls = F.get_urls(soup) #個別ページのURLを取得
              house_info, house_id = F.get_index_info(urls, data_list, house_id)

              browser.find_element_by_link_text('次へ').click()
              if page_count % 10 == 0:
                  logging.info("pages:{0}".format(page_count))
                  logging.info('==============================================')
                  time.sleep(60)
              time.sleep(60)

              houses_dict = {}
              img_list = []

              for house in house_info:
                  # Pandasで加工しやすいようにKeyが一つの辞書に家の情報を変更する
                  house_id, house_dict = F.edit_house_data(house)
                  houses_dict[house_id] = house_dict
                  # Houseの画像は変更が必要ないので、そのままリストに追加する
                  # ただ、一つづつ取り出して追加する必要があるので、要注意
                  img_list += house['imgs']

              attribute_df = pd.DataFrame(houses_dict).transpose()
              attribute_df.to_csv('csv/attribute_{filename}_{page_num}.csv'.format(filename = prefecture_name, page_num=page_count))
              imgs_df = pd.DataFrame(img_list)
              imgs_df.to_csv('csv/imgs_{filename}_{page_num}.csv'.format(filename = prefecture_name, page_num=page_count))

              page_count += 1

          except NoSuchElementException:
              browser.quit()
              break

      logging.info('browser quit')

def jalan():
    print('jalan')

def main(argv):
    if FLAGS.target == 'suumo':
        suumo()
    elif FLAGS.target == 'jalan':
	    jalan()

if __name__ == '__main__':
  app.run(main)