# -*- coding: utf-8 -*-

"""
Using frequency
===============

Using a dictionary of word frequency.
"""

# import multidict as multidict
from datetime import datetime
# import multiprocessing as mtp
from multiprocessing import cpu_count
from multiprocessing import Pool
# from multiprocessing import Queue
from multiprocessing import Manager

import numpy as np

# import os
import sys
import re
# import json
from PIL import Image
# from os import path
from wordcloud import WordCloud
# from wordcloud import STOPWORDS
from wordcloud import ImageColorGenerator
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import jieba
# from tqdm import tqdm
# from bilib import bilib


def runtime_record(runtime_):
    [delta_min, delta_sec] = divmod(runtime_.total_seconds(), 60)
    [delta_hour, delta_min] = divmod(delta_min, 60)
    print("\nRuntime--- %02d H: %02d M: %02d S" % (delta_hour, delta_min, delta_sec))


def get_cid_from_bv(bv):
    if bv.startswith('BV'):
        bv = bv[2:]
    url = f'https://www.bilibili.com/video/BV{bv}'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 '
                             '(KHTML, like Gecko) Chrome/55.0.2883.103 Safari/537.36'}
    response = requests.get(url=url, headers=headers)
    response.encoding = 'utf-8'
    html = response.text
    soup = BeautifulSoup(html, 'lxml')
    title = soup.select('meta[name="title"]')[0]['content']
    author = soup.select('meta[name="author"]')[0]['content']
    danmu_id = re.findall(r'cid=(\d+)&', html)[0]

    return {'status': 'ok', 'title': title, 'author': author, 'cid': danmu_id}


def makeImage(text, imgpath, stop_word):
    VUP_coloring = np.array(Image.open(imgpath))
    font_specify = f'C:\\Windows\\Fonts\\方正粗黑宋简体.ttf'
    wc = WordCloud(background_color="white",
                   font_path=font_specify,
                   max_words=1000,
                   mask=VUP_coloring,
                   stopwords=stop_word)

    # generate word cloud
    # wc.generate_from_frequencies(text)
    wc.generate(text)
    image_colors = ImageColorGenerator(VUP_coloring)

    # show
    # fig, axes = plt.subplots(1, 3)
    # axes[0].imshow(wc, interpolation="bilinear")
    # axes[1].imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
    # axes[2].imshow(VUP_coloring, cmap=plt.cm.gray, interpolation="bilinear")
    # for ax in axes:
    #     ax.set_axis_off()
    # plt.show()

    plt.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
    plt.axis("off")


def gen_wordcloud_one_video(bv, meme_img, l_stopwords):
    # VUP_meme_img = Path('./material/hxy_color.png')
    VUP_meme_img = meme_img
    d_info = get_cid_from_bv(bv)
    author = d_info['author']
    title = d_info['title']
    cid = d_info['cid']

    danmaku_txt = f'./texture/{author}-{bv}.txt'
    if not Path(danmaku_txt).is_file():
        url = f'http://comment.bilibili.com/{cid}.xml'
        req = requests.get(url)
        html = req.content
        html_doc = str(html, 'utf-8')
        soup = BeautifulSoup(html_doc, "lxml")
        results = soup.find_all('d')
        contents = [x.text for x in results]

        # danmaku_txt = f'./material/{author}-{bv}-{title}.txt'
        if not Path(f'./texture').is_dir():
            Path(f'./texture').mkdir(parents=True, exist_ok=True)
        # danmaku_txt = f'./texture/{author}-{bv}.txt'
        # if not Path(danmaku_txt).is_file():
        with open(danmaku_txt, 'w+', encoding='UTF-8') as f_zz:
            for danmaku_i in contents:
                f_zz.write(' '.join([word for word in jieba.cut(danmaku_i) if word not in l_stopwords]))
                f_zz.write('\n')

    text = open(danmaku_txt, encoding='utf-8')
    text = text.read()
    # makeImage(getFrequencyDictForText(text, stop_word), Path('./material/zz_color.png'))
    makeImage(text, VUP_meme_img, l_stopwords)
    if not Path(f'./{author}_archive').is_dir():
        Path(f'./{author}_archive').mkdir(parents=True, exist_ok=True)
    plt.savefig(f'./{author}_archive/{author}-{bv}-{title}.png')

    return title


def get_all_stream_record_bvlist(uid, sid):
    # m_videoid = []
    # url_recrod_series = f'https://space.bilibili.com/{uid}/channel/seriesdetail?sid={sid}8&ctype=0'
    url_recrod_series = f'https://api.bilibili.com/x/series/archives?mid=' \
                        f'{uid}&series_id={sid}&only_normal=true&sort=desc&pn=1&ps=30'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 '
                             '(KHTML, like Gecko) Chrome/55.0.2883.103 Safari/537.36'}
    response = requests.get(url=url_recrod_series, headers=headers)
    response.encoding = 'utf-8'
    html = response.text
    total_page = re.search(r'"total":(?P<bvid>\d+)', html).group(1)
    if total_page:
        url_recrod_series = f'https://api.bilibili.com/x/series/archives?mid=' \
                            f'{uid}&series_id={sid}&only_normal=true&sort=desc&pn=1&ps={total_page}'
        response = requests.get(url=url_recrod_series, headers=headers)
        response.encoding = 'utf-8'
        html = response.text

        m_videoid = re.findall(r'"bvid":"(?P<bvid>\w+)"', html)  # get full bvid list
        if m_videoid:
            return m_videoid
        else:
            sys.exit(1)
    else:
        sys.exit(1)


def job_increment(q, bvid, meme_img, l_stopwords, amount_bvids):
    title = gen_wordcloud_one_video(bvid, meme_img, l_stopwords)

    count_jobdone = q.get(True)
    count_jobdone += 1
    pct_done = count_jobdone/amount_bvids
    print(f'Job Finished: {count_jobdone} / {amount_bvids}  ~  {pct_done:.2%}  ->  {title}')
    q.put(count_jobdone)


def main(real_cores, inputdata) -> None:
    """
    Common Inpput
    :type real_cores: int
    :type inputdata: dict
    """

    # Data Expand
    l_bvid = inputdata['bvidlist']
    meme_img = inputdata['memeimg']
    l_stopwords = inputdata['stopwordslist']
    # UP_NAME = inputdata['UP_NAME']

    # Multi-process mode
    urpool = Pool(processes=real_cores)
    pool_list = []

    q_getconclusion = Manager().Queue()
    # count = 1
    q_getconclusion.put(0)
    amount_bvids = len(l_bvid)
    for bvid in l_bvid:
        pool_list.append(
            urpool.apply_async(
                job_increment, (
                    q_getconclusion, bvid, meme_img, l_stopwords, amount_bvids
                )
            )
        )
    urpool.close()
    urpool.join()

    print('Generate All WordClouds Done !')


def prepare_input():
    # bv = 'BV1ju411f7PG'
    l_common_stopwords = f'哈 哈哈 哈哈哈 哈哈哈哈 晚安 晚上 晚上好 拜拜 早上好'.split()

    UP_NAME = '红晓音'
    UP_UID = '899804'
    record_sid = '336578'
    meme_img = Path('./material/hxy_color3.png')

    # Stop Words Setting
    l_stopwords = l_common_stopwords
    l_special_stopwords = f'晓音 晓音姐 红晓音 音 音音 老板 草 阿晓 Call 问号 笑死 笑 死'.split()
    l_stopwords.extend(l_special_stopwords)
    stop_word_common_txt = Path(f'./material/stopwords.txt')
    with open(stop_word_common_txt, 'r+', encoding='UTF-8') as f_stop_word_common:
        for pure_word in f_stop_word_common.readlines():
            l_stopwords.append(pure_word.strip())

    # UP_NAME = '只只'
    # UP_UID = '495707763'
    # record_sid = '483701'
    # meme_img = Path('./material/zz_color.png')
    # l_special_stopwords = f'只 只只 只宝 草'.split()

    l_bvid = get_all_stream_record_bvlist(UP_UID, record_sid)

    d_resultinfo = {
        "bvidlist": l_bvid,
        "memeimg": meme_img,
        "stopwordslist": l_stopwords,
        "UP_NAME": UP_NAME,
    }

    return d_resultinfo


if __name__ == "__main__":

    start_time = datetime.now()

    # for bvid in tqdm(l_bvid, ascii=True, desc=f'Processing WordCloud for {UP_NAME}'):
    #     gen_wordcloud_one_video(bvid, meme_img, l_stopwords)

    cores = cpu_count()
    inputdata = prepare_input()
    main(cores, inputdata)

    end_time = datetime.now()
    runtime = end_time - start_time
    runtime_record(runtime)
