#from typeshed import NoneType
from typing import Union
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import requests
from bs4 import BeautifulSoup
import bs4

from selenium.common.exceptions import NoSuchElementException

import pandas as pd
from PIL import Image
import re
import io

import time

from absl import logging

def get_urls(soup:bs4.BeautifulSoup, target:str='suumo') -> list:
    """
        get_urls

        SUUMOの物件一覧のページからURL個別ページのURLを取得する関数

        1. SUUMOの物件情報(indexページ)は、基本的に内部リンク（'https:~がない"）形式でHTMLが作成されているため、内部リンクのみ全体のページから取得する
        2. 取得したURLをリスト形式にまとめる
        3. URLのリストを返す関数を作成する

        Args:
            soup (bs4.BeautifulSoup): SUUMOの物件一覧ページのbs4.BeautifulSoupオブジェクト。スクレイピングで取ってきた素のファイル

        Returns:
            list: SUUMOの物件データの各ページの内部リンクのURL (例 :['/chukoikkodate/yamagata/sc_tendo/nc_97027597/','/chukoikkodate/yamagata/sc_yamagata/nc_96589986/'])

        Examples:
            >>> get_urls (soup)
                [
                '/chukoikkodate/yamagata/sc_tendo/nc_97027597/',
                '/chukoikkodate/yamagata/sc_yamagata/nc_96589986/',
                '/chukoikkodate/yamagata/sc_yamagata/nc_97426196/',
                '/chukoikkodate/yamagata/sc_yamagata/nc_96140671/',
                '/chukoikkodate/yamagata/sc_sakata/nc_97073131/',
                '/chukoikkodate/yamagata/sc_higashimurayamagun/nc_96627907/',
                '/chukoikkodate/yamagata/sc_yamagata/nc_95997891/',
                '/chukoikkodate/yamagata/sc_higashimurayamagun/nc_97362727/',
                '/chukoikkodate/yamagata/sc_yamagata/nc_92020328/',
                '/chukoikkodate/yamagata/sc_yamagata/nc_95803869/',
                '/chukoikkodate/yamagata/sc_tendo/nc_94966659/',
                '/chukoikkodate/yamagata/sc_sakata/nc_94599713/',
                '/chukoikkodate/yamagata/sc_yamagata/nc_96872001/'
                ]
        """

    if target == 'suumo':
        h2_elems = soup.find_all('h2', attrs={'class' : 'property_unit-title'})
    elif target == 'jalan':
        h2_elems = soup.find_all('p', attrs={'class' : 'item-name'})

    urls = []

    for h2_elem in h2_elems:
        a_elem = h2_elem.find('a')
        url = a_elem.attrs['href']

        urls.append(url)

    return urls

def get_page_soup(internal_url:str, target:str='suumo') -> bs4.BeautifulSoup:
    """get_page_soup

        各物件へのリンクを作成して、アクセスして、各ページのsoupを出力する
        各ページの物件情報を収集する関数

        Args:
            internal_url (str): 内部リンクのURL

        Returns:
            bs4.BeautifulSoup: SUUMOの各ページからスクレイピングしてきた素のファイル

        Examples:

            >>> page_soup = get_page_soup ('url')
            >>> type(page_soup)
                bs4.BeautifulSoup
    """
    # ページ内リンクをドメインと結びつけて直にアクセスできるリンクに変換している
    if target == 'suumo':
        page_url = 'https://suumo.jp' + internal_url
    elif target == 'jalan':
        page_url = "https:" + internal_url + 'kuchikomi'

    page_res = requests.get(page_url)
    page_soup = BeautifulSoup(page_res.content, 'html.parser')

    time.sleep(15)

    return page_soup

def get_house_details(page_soup:bs4.BeautifulSoup) -> bs4.element.Tag:
    """get_house_details

        各ページの物件情報を収集する関数
        各物件ページのbs4.BeautifulSoupオブジェクトから「物件情報」にアクセスして、「物件情報」のテーブルまるごと取得する。
        出力は各ページの物件情報が格納されたbs4.element.Tagオブジェクト

        Args:
            page_soup (bs4.BeautifulSoup): 入力は各ページのsoup

        Returns:
            bs4.element.Tag: Tableが抽出されたbs4.element.Tagオブジェクト

        Examples:

            >>> get_house_details(page_soup）

        Note.
            テーブルはすべて二列というわけではないので、途中で要素がない場合があるため、is Noneで判別するようにしている。
    """
    #物件詳細のページへのリンクの取得
    house_details_a_elem = page_soup.find('a', attrs={'class' : 'tabOutline2'})

    if house_details_a_elem is None:
        house_details_a_elem = page_soup.find('a', attrs={'class' : 'tabOutline'})

    try:
        house_details_url = house_details_a_elem.attrs['href']

        #物件詳細のページへのアクセス
        house_details_res = requests.get(house_details_url)
        house_details_soup = BeautifulSoup(house_details_res.content, 'html.parser')

        # テーブルの取得
        house_details_info = house_details_soup.find('table', {'class': 'pCell10'})
        time.sleep(5)

    except Exception as e:
        logging.error(e)
        logging.error("house_details_a_elem", house_details_a_elem)
        logging.error("page_soup", page_soup)
        house_details_info = {}

    return house_details_info

def extract_table_data(table:bs4.element.Tag) -> dict:
    """extract_table_data

        各ページの物件情報を収集する関数
        各物件ページのbs4.BeautifulSoupオブジェクトから「物件情報」にアクセスして、「物件情報」のテーブルまるごと取得する。

        1. tableのHTMLからthとtd内の情報を取得する

        入力はtable要素
        出力はth要素がKey、td要素がValueになった辞書

        Args:
            table (bs4.element.Tag): 入力は各ページのtable要素（get_house_detailsの返り値をここでは想定）

        Returns:
            dict: SUUMOの各物件ページの物件情報が保存された辞書（Keyはカラム名,Valueがデータ）

        Examples:

            >>> extract_table_data(page_soup)
                {'築年数': '10年', …}

        Note.
            テーブルはすべて二列というわけではないので、途中で要素がない場合があるため、is Noneで判別するようにしている。
    """
    house_details_dict = {}

    for row in table.find_all('tr'):
        data_head = row.find_all('th')
        data_value = row.find_all('td')

        data_head_01 = data_head[0].text.replace('\n', '').replace('ヒント', '')
        data_value_01 = data_value[0].text.replace('\n', '').replace('\r', '').replace('\t', '')

        try:
            if data_head[1] is not None:
                data_head_02 = data_head[1].text.replace('\n', '').replace('ヒント', '')
                data_value_02 = data_value[1].text.replace('\n', '').replace('\r', '').replace('\t', '').replace('\u3000', '').replace('\xa0', '').replace('[乗り換え案内]', '')

                house_details_dict[data_head_01] = data_value_01
                house_details_dict[data_head_02] = data_value_02
        except IndexError:
            house_details_dict[data_head_01] = data_value_01

    return house_details_dict

def get_title_and_comment(page_soup:bs4.BeautifulSoup)->dict:
    """get_title_and_comment
        サイト上部にあるタイトルとコメントを取得する関数

        Args:
            page_soup (bs4.BeautifulSoup): 入力は各ページのbs4.BeautifulSoupオブジェクトを想定

        Returns:
            dict: SUUMOの各物件ページのタイトルとコメントが保存された辞書（例：{'title':'', 'comment':''}）

        Examples:

            >>> get_title_and_comment(page_soup)
                {'title':'', 'comment':''}
    """
    try:
        house_title = page_soup.find('h2', attrs = {'class' : 'fs16'})
        house_comment = page_soup.find('p', attrs = {'class' : 'fs14'})
        house_dict = {'title':house_title.text, 'comment':house_comment.text}
    except:
        house_dict = {'title':'', 'comment':''}
    return house_dict

def get_house_img(page_soup:bs4.BeautifulSoup, house_id:int)->list:
    """get_house_img
        各ページの写真を取得して、写真をHouseId_IMGIDの形式で保存する。
        家の画像の取得
        画像の名前を一意に決めるためにhouse_idを引数に入れている

        Args:
            page_soup (bs4.BeautifulSoup): 入力は各ページのbs4.BeautifulSoupオブジェクトを想定
            house_id（int）：その家の通し番号

        Returns:
            dict: SUUMOの各物件ページの画像と名前がセットになった辞書のリスト（例：[{'house_id':house_id, 'img_id':img_id, 'img_tag':img_tag, 'img_name':img_name）}...]

        Examples:

            >>> get_house_img(page_soup, house_id)
                [{'house_id':house_id, 'img_id':img_id, 'img_tag':img_tag, 'img_name':img_name）}...]
    """
    imgs = page_soup.find_all('img')
    img_list = list()
    img_id = 0
    # 以下で始まるのはIMGタグだがアクセスできないため排除する
    un_img_signal = 'gvavadfbasdfbarvbaebabaertbertbaebfbadbavafdvkavnakfvbaklvbaiklvuhiaerbnvnvkajbvkajbfgkjasbvkabvabfoak;dnvlasndvkahgvklashdvb'

    # 5の倍数のときに多めに休むようにしてみる
    sleep_count = 0
    for img in imgs:
        try:
            img_url = img['rel']
            img_tag = img['alt']
        except KeyError:
            img_url = un_img_signal
            img_tag = ""

        if not un_img_signal in img_url:
            img_name = str(house_id) + '_' + str(img_id)
            img_id += 1
            img_url = img_url.replace('&amp;', '&') # 文字化け対策
            # 以下は画像の保存に関する記述
            if not re.compile("resizeImage").search(img_url): #無条件で持ってくるとリサイズされた画像まで持ってきてしまうためそれを防ぐ
                logging.info("success", img_name, img_url) # 停止した場合どこで停止しているかを確認するため
                # 画像がリサイズされていないときは保存する
                img = Image.open(io.BytesIO(requests.get(img_url).content))
                img.save(f'imgs/suumo/{img_name}.jpg')
                img_list.append({'house_id':house_id, 'img_id':img_id, 'img_tag':img_tag, 'img_name':img_name})
                time.sleep(10)
                # 10枚画像取るごとにちょっとながめに休憩
                if sleep_count % 10 == 0:
                    time.sleep(50)
                sleep_count += 1
            else:
                logging.error("false")

    return img_list

def get_index_info(urls:list, house_info:list, house_id:int) -> Union[list, int]:
    """get_index_info
        Index1ページ分のURL
        ここのループでは、Index1ページ分のURLをすべて取ってきている

        Args:
            urls (list): 一つのindexページに表示されているページすべてのURLがはいったリスト（ここでは、get_urlsの出力を想定
            house_info(list) : すべてのハウス情報を記録するためのリスト
            house_id（int）：その家の通し番号

        Returns:
            dict: SUUMOの各物件のすべての情報が含まれている辞書のリスト（例：[{'House_ID': house_id, 'text':house_text_dict, 'info':house_info_dict, 'imgs':house_img_list}...]

        Examples:

            >>> get_index_info(urls, house_info, house_id)
                [{'House_ID': house_id, 'text':house_text_dict, 'info':house_info_dict, 'imgs':house_img_list}...]
    """
    for url in urls:
        logging.info("property's page URL : ", url)
        page_soup = get_page_soup(url)# requestをget_page_soupは送って個々の物件の情報を取得している
        table = get_house_details(page_soup) # request送って物件詳細のテーブル情報を取得している
        try:
            house_info_dict = extract_table_data(table)
        except:
            logging.warning("get_index_info Error")
            house_info_dict = {'販売スケジュール': "",
        'イベント情報': "",
        '所在地' : "",
        '交通' : "",
        '販売戸数' :"",
        '総戸数' : "",
        '価格' : "",
        '最多価格帯' : "",
        '私道負担・道路' : "",
        '諸費用' : "",
        '間取り' : "",
        '建物面積' : "",
        '土地面積' : "",
        '建ぺい率・容積率' : "",
        '完成時期(築年月)' : "",
        '入居時期' : "",
        '土地の権利形態' : "",
        '構造・工法' : "",
        '施工' : "",
        'リフォーム' : "",
        '用途地域' : "",
        '地目' : "",
        'その他制限事項' : "",
        'その他概要・特記事項' : ""}
        house_text_dict = get_title_and_comment(page_soup)
        house_img_list = get_house_img(page_soup, house_id) # request送って写真を取得している

        house_dict = {'House_ID': house_id, 'text':house_text_dict, 'info':house_info_dict, 'imgs':house_img_list}
        house_info.append(house_dict)

        house_id += 1

        time.sleep(20)

    return house_info, house_id

def edit_house_data(house:dict) -> Union[int, dict]:
    """edit_house_data
        Index1ページ分のURL
        ここのループでは、Index1ページ分のURLをすべて取ってきている

        Args:
            house (dict): 一つ一つの家の情報が入っている辞書（ここでは、get_index_infoの返り値の第一引数を仮定）

        Returns:
            dict: あとからPandasで変換しやすいようにすべてのカラムを辞書形式に変換したもの
            int: 家固有のID

        Examples:

            >>> edit_house_data(house)
                int, dict
    """
    house_id = house['House_ID']
    house_dict = {
        'title' : house['text']['title'],
        'comment' : house['text']['comment'],
        '販売スケジュール' : house['info']['販売スケジュール'],
        'イベント情報' : house['info']['イベント情報'],
        '所在地' : house['info']['所在地'],
        '交通' : house['info']['交通'],
        '販売戸数' : house['info']['販売戸数'],
        '総戸数' : house['info']['総戸数'],
        '価格' : house['info']['価格'],
        '最多価格帯' : house['info']['最多価格帯'],
        '私道負担・道路' : house['info']['私道負担・道路'],
        '諸費用' : house['info']['諸費用'],
        '間取り' : house['info']['間取り'],
        '建物面積' : house['info']['建物面積'],
        '土地面積' : house['info']['土地面積'],
        '建ぺい率・容積率' : house['info']['建ぺい率・容積率'],
        '完成時期(築年月)' : house['info']['完成時期(築年月)'],
        '入居時期' : house['info']['入居時期'],
        '土地の権利形態' : house['info']['土地の権利形態'],
        '構造・工法' : house['info']['構造・工法'],
        '施工' : house['info']['施工'],
        'リフォーム' : house['info']['リフォーム'],
        '用途地域' : house['info']['用途地域'],
        '地目' : house['info']['地目'],
        'その他制限事項' : house['info']['その他制限事項'],
        'その他概要・特記事項' : house['info']['その他概要・特記事項'],
    }

    return house_id, house_dict



# jalan only function
def is_existing_img(content_soup:bs4.BeautifulSoup) -> Union[None, bs4.element.Tag]:
    img_existing = content_soup.find('picture', attrs={'class' : 'item-mainImg'})
    return img_existing

def get_review_page_soup(content_soup:bs4.BeautifulSoup):
    div_elem = content_soup.find('p', attrs={'class' : 'item-title'})
    # details page url
    a_elem = div_elem.find('a')
    review_page_url = 'https:' + a_elem.attrs['href']
    # ここはクラスにしてselfに入れる
    # review_property_dict['review_page_url'] = review_page_url
    review_page_res = requests.get(review_page_url) #details page soup
    review_page_soup = BeautifulSoup(review_page_res.content, 'html.parser')

    return review_page_soup

def get_jalan_review(review_id:int, content_soup:bs4.BeautifulSoup, review_page_soup:bs4.BeautifulSoup) -> dict:
    review_property_dict = {}
    review_property_dict['review_id'] = review_id
    
    div_elem = content_soup.find('p', attrs={'class' : 'item-title'})
    a_elem = div_elem.find('a')
    review_page_url = 'https:' + a_elem.attrs['href']
    review_property_dict['review_page_url'] = review_page_url

    review_soup = review_page_soup.find('p', attrs={'class' : 'reviewText'})

    title = review_page_soup.find('h1', attrs={'class' : 'basicTitle'})
    try:
        review = review_soup.text.replace('\n', '')
    except:
        review = ''

    review_property_dict['title'] = title
    review_property_dict['review'] = review

    review_properties = review_page_soup.find('ul', attrs={'class' : 'reviewDetail'})
    review_properties = review_properties.find_all('li')
    review_properties=[review_property.text.strip() for review_property in review_properties]
    text = str(review_properties[0])

    for review_property in review_properties:
      column_name = review_property.split('：')[0]
      column_data = review_property.split('：')[1]

      review_property_dict[column_name] = column_data

    return review_property_dict

def get_review_img(landmark_id:int, review_id:int, review_page_soup:bs4.BeautifulSoup)->list:
    # img_urls = []
    img_id = 0
    img_name_list = list()
    # print('img class')

    img_contents_block = review_page_soup.find('ul', attrs={'class' : 'cassetteList-photo'})
    # print('img contents block', img_contents_block)
    img_contents = img_contents_block.find_all('li', attrs={'class' : 'lightbox'})
    # print('img contents', img_contents)

    for img_content in img_contents:
      img_elem = img_content.find('source')
      img_url = img_elem.attrs['srcset']
      img_url = 'https:' + img_url

      img = Image.open(io.BytesIO(requests.get(img_url).content))
      img_name=str(landmark_id) + '_' + str(review_id) + '_' + str(img_id)
      img.save(f'imgs/jalan/{img_name}.jpg')
      
      img_name_list.append(img_name)

      img_id += 1

    return img_name_list