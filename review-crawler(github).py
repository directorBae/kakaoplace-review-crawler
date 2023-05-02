from selenium import webdriver
import pandas as pd
import numpy as np

from bs4 import BeautifulSoup
import re
import time

import warnings
warnings.filterwarnings("ignore")

from selenium.webdriver.common.by import By
import requests

class review_crawler:
    def __init__(self):
        self.API_KEY = "INSERT-YOUR-API-KEY-HERE"
        self.page_urls = {}
        
    def get_URL(self, name_list):
        for name in name_list:
            url = f"https://dapi.kakao.com/v2/local/search/keyword.json?query={name}"
            result = requests.get(url, headers={"Authorization": f"KakaoAK {self.API_KEY}"})
            com_url = result.json()['documents'][0]['place_url']
            m_url = com_url.replace('.com/', '.com/m/')
            self.page_urls[name] = m_url
        return self.page_urls
    
    def get_review(self, path, name_list):
        
        urls = self.get_URL(name_list)

        columns = ['name', 'score', 'review']
        df = pd.DataFrame(columns=columns)  # 컬럼만 조회
        driver = webdriver.Chrome(path)  # 브라우저 실행

        names = [] # 식당 이름
        reviews = []
        rates = []

        for name in name_list:
            urls[name]+="#comment"
            driver.get(urls[name])
            time.sleep(1)
            last_height = driver.execute_script("return document.body.scrollHeight")
            driver.execute_script(f"window.scrollTo(0, {last_height});")
            time.sleep(1)

            while(1):
                try:
                    button = driver.find_element(By.CSS_SELECTOR, '#mArticle > div:nth-child(15) > div > div.cont_grade > a')
                    print("t:",button.text)
                    if button.text == "후기 더보기":
                        driver.execute_script("arguments[0].click();", button)
                        time.sleep(0.5)
                    else:
                        break
                except:
                    break
            time.sleep(1)

            html = driver.page_source  # html 소스 데이터 (page 소스를 html에 세팅)
            soup = BeautifulSoup(html, 'html.parser')

            contents_div = soup.find(name='ul', attrs={"class": "list_grade"})  # 리뷰 영역. 별점, 내용
            r = contents_div.find_all(name="span", attrs={"class": "ico_star inner_star"})  # 별점값 목록
            
            for rate in r:
                style_attr = rate.attrs.get('style')
                percentage_str = style_attr.split(':')[1].strip(';')
                percentage = int(percentage_str[:-1])
                star = int(percentage/100*5)
                rates.append(star)
                names.append(name)

            review = contents_div.find_all(name="p", attrs={"class": "txt_comment"})  # 리뷰 목록
            for p_review in review:
                span_tag = p_review.find('span')
                text = str(span_tag).strip("<span>").strip("</span>")
                text = text.replace("<br/>",". ").replace("\n",". ")
                reviews.append(text)

        df['name'] = names
        df["score"] = rates
        df["review"] = reviews
        driver.close()
        df.to_json(path+'reviews.json')
        return df