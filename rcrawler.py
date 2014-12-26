# -*- coding: utf-8 -*-↲

import time
import codecs, sys
import os
import urllib2
import datetime
from bs4 import BeautifulSoup ,  NavigableString, Declaration, Comment


# TODO: timestampは統一
# TODO: ファイル名を綺麗に, 保存も綺麗に

# TODO: Google, Amazon対応


sys.stdout = codecs.getwriter("utf-8")(sys.stdout)

# listをcsv形式に変換
def makecsv(data):
    csv = u""

    for num in range(len(data)):
        
        data[num] = data[num].replace(',','.') # エラーになりそうなのは排除
        csv += "\"" + data[num] + "\""
        
        if num != len(data) - 1:
            csv += ","
        else:
            csv += "\n"

    return csv

def wordsfromcsv(nfile):
    words = []

    # sjisで読み込みたかったけど挫折
    
#    fi = codecs.open(nfile, "r", "shift_jis")    
#    for line in fi:
#        words = line.rstrip('\r\n')

#    for word in words:
#        wordu.append(word.encode('shift_jis'))
#   
#    return wordu
    
    
    # utf8のテキストから読み込み
    for line in codecs.open(nfile, 'r', 'utf-8'):
        words.append(line.rstrip())
#        words.append(unicode(line))

    return words

def crawl(words, pmax):

    # タイムスタンプは起動時
    stime = datetime.datetime.now().isoformat().replace('T','-').replace(':','-').replace('.','-')
#    stime = stime + "-" + word.encode('utf-8')
    os.system('mkdir ' + stime)
   
    # 楽天をクロール
    rcrawl(words, pmax, stime)

    # Amazonをクロール
#    acrawl(words, pmax, stime, words)

    # Googleをクロール
#    gcrawl(words, pmax, stime, words)



def rcrawl(words, pmax, stime):
    # words -> urls 変換
    urls = wordstourlsR(words)

    # 楽天のディレクトリ作成
    os.system('mkdir ' + stime + '/Rakuten')
   
    # 全てのseed urlに対して
    for n in range(len(urls)):

        # urlと, 今相手にしてるwordのget
        url = urls[n]
        word = words[n]

        # ディレクトリ作成
        path = stime + '/Rakuten/' + word.encode('utf-8')
        picpath = stime + '/Rakuten/' + word.encode('utf-8')
        os.system('mkdir ' + picpath)

        # ファイルの一行目用意
        column = [u"no", u"name", u"url", u"caption", u"shopname", u"shopurl", u"price"]

        # 出力用ファイル準備 & 一行目追加
        fname = ''
        fname = path + '.csv'
        f = open(fname, 'w')
        f.write(makecsv(column).encode('utf-8'))

        # item数, page数のリセット
        nitem = 0
        npage = 0
        
        time.sleep(0.5)

        while pmax > nitem :
            npage += 1

            # 次ページget
            nurl = getnexturlR(word, npage)

            # htmlリーダ & パーサ準備
            c = urllib2.urlopen(nurl)
            soup = BeautifulSoup(c.read())

            products = soup.find(id="rsrWrapper").find(id="tableHeader").find(id="rsrContainer").find(id="rsrMainContents").find(id="rsrMainArea").find(id="rsrMainSect").find(id="ratArea").find_all('div')

            # それぞれの商品に対して
            for product in products:

                # 商品数がMAXを超えていなかったら
                if nitem < pmax:
                    title       = u""
                    url         = u""
                    photourl    = u""
                    caption     = u""
                    shopname    = u""
                    shopurl     = u""
                    price       = 0
                    data        = []

                    # 商品説明とか商品タイトルとかを順に検索
                    for container in product.find_all('div'):

                        # classを属性に持ってるか?チェック
                        if "class" in container.attrs:

                            # 画像保存
                            if container['class'] and u'rsrSResultPhoto' in container['class']:
                                nitem += 1 # この属性を持っていることを商品数+1とみなす
                                data.append(unicode(nitem))
                                print "NO       : " + unicode(nitem)
                                
                                photourl = container.img['src']
                                photo = urllib2.urlopen(photourl)
                                pf = open(picpath + '/' + str(nitem) + '.png', 'wb')
                                pf.write(photo.read())
                                pf.close()

                            # タイトル & キャプション & LPのURL & お店の名前 & お店のURL の保存
                            # ちなみに.. webページの構造が変化するとマズいYo
                            if u'rsrSResultItemTxt' in container['class']:
                                title    = container.h2.a.string
                                url      = container.h2.a.get('href')
                                if container.p != None :
                                    caption = container.p.string
                                else:
                                    caption = ""
                                shopname = container.findAll('span')[1].a.string
                                shopurl  = container.findAll('span')[1].a['href']
                                
                                data.append(title)
                                data.append(url)
                                data.append(caption)
                                data.append(shopname)
                                data.append(shopurl)
                                
                                print "TITLE    : " + title
                                print "URL      : " + url
                                print "CAPTION  : " + caption
                                print "SHOPNAME : " + shopname
                                print "SHOPURL  : " + shopurl

                            # 値段とか
                            if u'rsrSResultItemInfo' in container['class']:
                                price   = container.findAll('p')[0].a.contents[0]

                                data.append(price)

                                print "PRICE    : " + price + "\n" 


                    # ファイル出力
                    if len(data) > 0:
                        info = u""
                        info = makecsv(data)
                        f.write(info.encode("utf-8"))

        # 終了時処理
        f.close() #ファイルオブジェクトを閉じとく
        # Excelで読めるよう, utf8 -> sjis変換
        os.system('nkf -s --overwrite ' + './' + fname)

# 楽天用, 次ページurl取得
def getnexturlR(word, npage):
    
    url = "http://search.rakuten.co.jp/search/mall/" \
        + urllib2.quote(word.encode('utf-8')) \
        + "/-/p." \
        + str(npage) \
        + "-s.1-sf.0-st.A-v.2?grp=product"

    return url

# 楽天用, 文言 -> seed url変換
def wordstourlsR(words):

    urls = []
    for word in words:
        word = urllib2.quote(word.encode('utf-8'))
        url = "http://search.rakuten.co.jp/search/mall/" + word + "/-/st.A?grp=product"
        urls.append(url)

    return urls

if __name__ == "__main__":

    # 商品数
    pmax = 400
    
    # 検索文言ファイル名
    fname = "list.txt"

    # 捜索
    crawl(wordsfromcsv(fname), pmax)


