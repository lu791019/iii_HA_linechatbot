#!/usr/bin/env python
# coding: utf-8

# In[1]:


'''line bot 的固定設置'''
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import json
import  pymysql 

app = Flask(__name__,static_url_path = "/image" , static_folder = "./image/")


secretFileContentJson=json.load(open("line_secret_key.txt",'r'))
server_url=secretFileContentJson.get("server_url")


line_bot_api = LineBotApi(secretFileContentJson.get("channel_access_token"))
handler = WebhookHandler(secretFileContentJson.get("secret_key"))

@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


# In[2]:


'''各種信息格式設定'''

from linebot.models import *

# 圖片消息的基本建構特徵
# image_message1 = ImageSendMessage(
#     original_content_url='https://%s/image/headache.jpg' % server_url,
#     preview_image_url='https://%s/image/headache.jpg' % server_url
# )


# 迎新消息
reply_message_new = [
    TextSendMessage(text="歡迎使用健康助手,請使用下方圖文選單進行操作")
]

# [::test::]醫院信息
reply_message_info = [
    TemplateSendMessage(
    alt_text='Buttons template',
    template=ButtonsTemplate(
        thumbnail_image_url="https://%s/image/hospital.jpg"% server_url,
        title='資策會醫院',
        text='台北市大安區和平東路二段106號',
        actions=[
          {
            "type": "uri",
            "label": "**撥打** 醫院電話",
            "uri": "tel://33456789"
          },
          {
            "type": "uri",
            "label": "**導航** 醫院地址",
            "uri": "line://app/1599834661-1RXo0B54"
          }
        ],
)
)
]


#[::test::]可以直接get的功能字典
template_message_dict = {
    "[::test::]醫院信息":reply_message_info,
    "[::test::]頭部":TextSendMessage(text="建議您掛：一般內科、家庭醫學科、神經內科、眼科、耳鼻喉科、皮膚科、精神科。"),
    "[::test::]胸部":TextSendMessage(text="建議您掛：心臟內科、胸腔內科、一般內科、家庭醫學科。"),
    "[::test::]手部":TextSendMessage(text="建議您掛：骨科、復健科、神經內科、神經外科、家庭醫學科、皮膚科。"),
    "[::test::]腿部":TextSendMessage(text="建議您掛：骨科、復健科、神經內科、神經外科、家庭醫學科、皮膚科、過敏免疫風濕科。"),
    "[::test::]腹部":TextSendMessage(text="建議您掛：胃腸科、一般內科、家庭醫學科、一般外科、腎臟科、疼痛控制科。"),
    "[::test::]生殖部":TextSendMessage(text="建議您掛：婦產科、泌尿科、腎臟科。"),
    "[::test::]背部":TextSendMessage(text="建議您掛：骨科、復健科、心臟內科、胸腔內科、神經內科、神經外科、疼痛控制科。"),
    "[::test::]臀部":TextSendMessage(text="建議您掛：一般內科、胃腸科、直腸外科、家庭醫學科。"),
    "[::test::]腰部":TextSendMessage(text="建議您掛：復健科、骨科、神經內科、疼痛控制科、腎臟科。")
    }


# In[3]:


'''[::test::]確認預約'''
import pandas as pd
import datetime
from linebot.models import *

def checkbooking(user_id):
    try:
        conn  =  pymysql.connect(host = secretFileContentJson.get("host"), user = secretFileContentJson.get("user"), passwd = secretFileContentJson.get("passwd"),db=secretFileContentJson.get("db")) 
        cur  =  conn.cursor() 
        sql = "select * from Plist;"
        Plist = pd.read_sql(sql, con=conn)
    finally:
        if cur: cur.close() 
        if conn: conn.close()
    #把開始日期轉成時間格式
    Plist.SDATE=pd.to_datetime(Plist.SDATE,format='%Y/%m/%d %H:%M')
    #按開始時間重新排序
    Plist=Plist.sort_index(by=['SDATE'],ascending=True).reset_index(drop=True)
    today=datetime.datetime.now()
    replay=[]
    #user_id=event.source.user_id
    #如果LineID沒有在df裡面,要求輸入病患編碼
    if len(Plist[Plist['lineID']== user_id]) == 0:
        return(TextSendMessage(text="您的病患編碼尚未綁定,請輸入您的病患編碼"))
    #如果LineID在df裡面
    if len(Plist[Plist['lineID']== user_id]) >0:
        #bookingcount 有幾筆預約
        bookingcount = 0
        #bookingindex預約的index
        bookingindex=[]
        pno=""
    #取出符合LineID且在預約時間在未來(日期大於今天)的row index
        for j in Plist[Plist['lineID']== user_id].SDATE.index:
            if Plist.SDATE[j] > today:
                #bookingindex預約次數
                bookingcount += 1
                #bookingindex預約的index
                bookingindex.append(j)
    #判斷共有幾筆預約,若大於0則回傳檢查信息
        if bookingcount > 0:
            PNO=Plist['PNO'][bookingindex[0]]
            #要回復的文字加入replay
            replay.append(TextSendMessage(text="病患編碼:%s您好!\n您目前有%s個預約檢查" % (PNO,bookingcount)))
            booking=""
            for i in range(len(bookingindex)):
                index=bookingindex[i]
                booking=booking +"\n第%s個檢查:\n檢查時間: %s\n檢查地點: %s\n***************" % (i+1 , Plist['SDATE'][index],Plist['PLACE'][index])
            replay.append(TextSendMessage(text=booking))
            replay.append(TextSendMessage(text="請注意檢查前6小時應禁食、禁酒及飲料、禁止輸入葡萄糖，避免劇烈或長時間運動。"))
            return(replay)
        if bookingcount == 0:
            return(TextSendMessage(text="您當前沒有預約檢查"))
        
        


# In[4]:


'''添加病患編碼'''
#添加病患編碼,只要回復的文字有至少有6個的純數字, 就按病患編碼lineID加入plist
#引入所需要的消息與模板消息
from linebot.models import *

#引入按鍵模板
from linebot.models.template import *

def ADDPNO(user_id,PNO):
    PNO=int(PNO)
    try:
        conn  =  pymysql.connect(host = secretFileContentJson.get("host"), user = secretFileContentJson.get("user"), passwd = secretFileContentJson.get("passwd"),db=secretFileContentJson.get("db")) 
        cur  =  conn.cursor() 
        sql = "select * from Plist;"
        Plist = pd.read_sql(sql, con=conn)
    finally:
        if cur: cur.close() 
        if conn: conn.close()
            
    #如果沒有這個病歷碼,就要重新操作
    if len(Plist[Plist['PNO']== PNO]) == 0:
        return(TextSendMessage(text="您輸入的病患編碼有誤,請重新輸入"))
    #如果已經有綁定別的病歷碼,會彈出確認選單是否要刪除綁定
    if len(Plist[Plist['lineID']== user_id]) >0:
        oldPNO=Plist[Plist['lineID']== user_id]["PNO"].value_counts().index[0]
        return(TemplateSendMessage(
        alt_text="this is a confirm template",
        template=ConfirmTemplate(
            title='是否先解除綁定的病患編碼?',
            text='您已綁定病患編碼:%s,請問是否先解除綁定的病患編碼?'% oldPNO,
            actions=[
              {
                "type": "postback",
                "label": "是",
                "data": "[::test::]重新綁定"
              },
              {
                "type": "message",
                "label": "否",
                "text": "否"
              }],)))
    if len(Plist[Plist['lineID']== user_id]) ==0:
        if len(Plist[Plist['PNO']== PNO]) > 0:
            try:
                conn  =  pymysql.connect(host = secretFileContentJson.get("host"), user = secretFileContentJson.get("user"), passwd = secretFileContentJson.get("passwd"),db=secretFileContentJson.get("db")) 
                cur  =  conn.cursor() 
                cur.execute( "UPDATE Plist SET lineID='%s' WHERE PNO=%s;" % (user_id,PNO) ) 
                #注意有修改一定要commit
                conn.commit()
            finally:
                if cur: cur.close() 
                if conn: conn.close() 
            return(TextSendMessage(text="病患編碼已添加成功!請重新操作圖文選單"))
        
        
    


# In[5]:


'''協同過濾，文章推薦演算'''

import pandas as pd
import  pymysql 
from math import sqrt

def get_logs():
    try:
        conn  =  pymysql.connect(host = secretFileContentJson.get("host"), user = secretFileContentJson.get("user"), passwd = secretFileContentJson.get("passwd"),db=secretFileContentJson.get("db")) 
        cur  =  conn.cursor() 
        cur.execute( "select lineID, time, tag_g from click_log order by lineID, time desc;" ) 
        df = pd.DataFrame(cur, columns=["lineID", "time", "tag_g"])
        return df
    finally:
        if cur: cur.close() 
        if conn: conn.close()

def weighting(user_dict:dict) -> dict:
    """從log算出分數，並編排成裕處理的格式"""
    result_list = [] 
    for key in user_dict.keys():
    # 按照點擊文章時間加權(ex: 最新3篇*1, 次新3篇*0.5, 再次三篇*0.2), 同key 相加 
        wt_dict = {}
        for i in range(len(user_dict[key])):
            k = user_dict[key][i][0]
            v = (1 if i in [0,1,2] else 0.5 
                    if i in [3,4,5] else 0.2 )
            wt_dict[k] = v if k not in wt_dict else wt_dict[k]+v
            if i == 8: break
        for kk in wt_dict.keys():
            result_list.append((key, (kk, wt_dict[kk])))
    return result_list

# 資料整理需要的function
def remove_duplicates(userRatings):
    tag1, rating1 = userRatings[1]
    tag2, rating2 = userRatings[2]
    return tag1 < tag2

def make_tag_pairs(userRatings):
    (tag1, rating1) = userRatings[1]
    (tag2, rating2) = userRatings[2]
    return ((tag1, tag2), (rating1, rating2))

def compute_score(ratingPairsList):
    ratingPairs = ratingPairsList[1]
    numPairs = 0
    sum_xx = sum_yy = sum_xy = 0
    for ratingX, ratingY in ratingPairs:
        sum_xx += ratingX * ratingX
        sum_yy += ratingY * ratingY
        sum_xy += ratingX * ratingY
        numPairs += 1

    numerator = sum_xy
    denominator = sqrt(sum_xx) * sqrt(sum_yy)
    score = 0
    if (denominator):  # 避免分母為0
        score = (numerator / (float(denominator)))
    
    return ratingPairsList[0], (score, numPairs)

# 資料整理結束，算cos similarity
def search_similar(group, tag_pair_with_scores_list, s_threshold=0.85, a_threshold=1):
    similarity_threshold = s_threshold
    appearence_threshold = a_threshold
    tag = group
    result = list(filter(lambda x: (x[0][0] == tag or x[0][1] == tag)
                            and x[1][0] > similarity_threshold 
                            and x[1][1] > appearence_threshold,
                            tag_pair_with_scores_list))
    if len(result) != 0:
        return tuple(i[0][1] for i in result)
    else:
        return None

# out put: 根據cos similarity 推 5 篇文章，輸出成 dataframe
# 更改相似度要求與最少點擊人數
def get_recommend_article(log_tag, tag_pair_with_scores_list, s=0.85, a=1):
    try:
        conn  =  pymysql.connect(host = secretFileContentJson.get("host"), user = secretFileContentJson.get("user"), passwd = secretFileContentJson.get("passwd"),db=secretFileContentJson.get("db")) 
        cur  =  conn.cursor() 
        similar = search_similar(log_tag, tag_pair_with_scores_list, s_threshold=s, a_threshold=a)  # 搜尋最相近的文章tag
        if similar is not None:
            if len(similar) == 1:
                cur.execute( f"select * from healthy_group28 where tag_g in ({similar[0]});" ) 
            else:
                cur.execute( f"select * from healthy_group28 where tag_g in {similar};" ) 
        else:
            cur.execute( f"select * from healthy_group28 where tag_g in ({log_tag});" )
        df = pd.DataFrame(cur, columns=["title","URL","Published date","keywords","KW","picture","group"])
        return df
    finally:
        if cur: cur.close() 
        if conn: conn.close()


def recommend_five_article(tag_tag: int):
    # 讀取log
    df = get_logs()

    # 將log 轉換成dict 準備輸入weighting
    user_dict = {}
    for line in range(len(df)):
        userid, logtime, tag= list(df.loc[line])
        if userid not in user_dict:
            user_dict[userid]=[]
        user_dict[userid].append((tag, logtime))

    # 得到與movie_rating 相同格式
    cos_df = pd.DataFrame(weighting(user_dict))
    cos_df.columns = ['id', 'rate']

    # 開始資料整理
    self_joined_ratings = cos_df.merge(cos_df, on='id', how='inner')

    self_joined_ratings_list = self_joined_ratings.values.tolist()
    distinct_self_joined_ratings_list = list(filter(remove_duplicates, self_joined_ratings_list))

    tag_pairs_list = list(map(make_tag_pairs, distinct_self_joined_ratings_list))

    # groupByKey
    tag_pairs_list.sort(key=lambda x:x[0])
    tag_pair_ratings_list = []
    new_in_list = []
    prev_a = None
    for t in tag_pairs_list:
        a, b = t[0], t[1]
        if prev_a is None or a == prev_a:
            new_in_list.append(b)
        else:
            tag_pair_ratings_list.append((prev_a, new_in_list))
            new_in_list = [b]
        prev_a = a
    tag_pair_ratings_list.append((a, new_in_list))

    # 算分數
    tag_pair_with_scores_list = list(map(compute_score, tag_pair_ratings_list))

    # 得到五篇推薦的文章
    adf = pd.DataFrame(get_recommend_article(tag_tag, tag_pair_with_scores_list)).sample(2)

    try:
        conn  =  pymysql.connect(host = secretFileContentJson.get("host"), user = secretFileContentJson.get("user"), passwd = secretFileContentJson.get("passwd"),db=secretFileContentJson.get("db")) 
        cur  =  conn.cursor() 
        cur.execute( f"select * from healthy_group28 where tag_g in ({tag_tag});" )  
        bdf = pd.DataFrame(cur, columns=["title","URL","Published date","keywords","KW","picture","group"]).sample(2) 
    finally:
        if cur: cur.close() 
        if conn: conn.close()
            
            
    try:
        conn  =  pymysql.connect(host = secretFileContentJson.get("host"), user = secretFileContentJson.get("user"), passwd = secretFileContentJson.get("passwd"),db=secretFileContentJson.get("db")) 
        cur  =  conn.cursor() 
        cur.execute( f"select * from healthy_group28;" )  
        cdf = pd.DataFrame(cur, columns=["title","URL","Published date","keywords","KW","picture","group"]).sample(2)
    finally:
        if cur: cur.close() 
        if conn: conn.close()
            
    return (pd.concat([bdf,adf,cdf],axis=0))


# In[6]:


'''將要推荐的文章放進一個df（也就變數article），df丟入article_recommend_eval轉成line格式'''
import random
import datetime
from linebot.models import *
import pandas as pd
from jieba.analyse import extract_tags,set_stop_words
from jieba import cut, set_dictionary, load_userdict,lcut,cut_for_search


def article_recommend_eval(article):
    
    #NO=random.randint(0,(len(df.title)-5))
    #article =  df[NO:(NO+5)].reset_index(drop=True)
    head = "TemplateSendMessage(alt_text='Carousel template',template=CarouselTemplate(columns=["
    end = "]))"

    for i in range(len(article)):
        add = "CarouselColumn(thumbnail_image_url= '%s',title='%s',text= '關鍵字:'+'%s', "               "actions=[PostbackTemplateAction(label= '點擊閱讀',data= '%s')])" %               (article.picture[i],article.title[i],article.keywords[i],article.URL[i])
        head=head+add+','
    head=head+end
    return(eval(head))


# In[7]:


'''根據關鍵字搜尋出5篇文章'''
import random
import datetime
from linebot.models import *
import pandas as pd
from jieba.analyse import extract_tags,set_stop_words
from jieba import cut, set_dictionary, load_userdict,lcut,cut_for_search

#根據关键字搜寻出5篇文章：
def article_from_key(article_key,df):
    list=extract_tags(article_key)
    if "吃" in article_key:
        list.append("飲食")
    if "睡" in article_key:
        list.append("睡")
    if "瘦" in article_key:
        list.append("瘦")
    if "胖" in article_key:
        list.append("減肥")
    if "肥" in article_key:
        list.append("減肥")
    if len(list) <= 0 :
        nothing="文字沒有被辨識到哦, 請換個方式問問看"
        return(TextSendMessage(text=nothing))
    if len(list) > 0 :
        c = ["picture","title","keywords","URL"]
        article = pd.DataFrame(columns=c)
        for i in range (len(list),0,-1):
            for k in range(len(df)):
                x = 0
                for l in list:
                    if l in df["title"][k]:
                        x += 1
                if x == i:
                    data = [df.picture[k],df.title[k],df.keywords[k],df.URL[k]]
                    s = pd.Series(data, index=c)
                    article = article.append(s, ignore_index=True) 
            for k in range(len(df)):
                x = 0
                for l in list:
                    if l in df["keywords"][k]:
                        x += 1
                if x == i:
                    data = [df.picture[k],df.title[k],df.keywords[k],df.URL[k]]
                    s = pd.Series(data, index=c)
                    article = article.append(s, ignore_index=True)
        if len(article)==0:
            nothing="文字沒有被辨識到哦, 請換個方式問問看"
            return(TextSendMessage(text=nothing))
        if len(article)>0:
            return(article_recommend_eval(article.head(5)))


# In[8]:



'''文章推薦邏輯'''

#客户点击文章推荐-》 是否有点击过文章-》有点击过文章，根据点击过的文章做推荐
#                              -》没有点击过文章，确认是否有配对病历码（提示登陆病例码）-》有病例码，根据看诊内容给推荐文章
#                                                                                -》没有病例码，随机推送文章

import random
import datetime
from linebot.models import *
import pandas as pd
from jieba.analyse import extract_tags,set_stop_words
from jieba import cut, set_dictionary, load_userdict,lcut,cut_for_search


        

#确认是否有点击过文章或病例码
def article__recommend(user_ID):
    try:
        conn  =  pymysql.connect(host = secretFileContentJson.get("host"), user = secretFileContentJson.get("user"), passwd = secretFileContentJson.get("passwd"),db=secretFileContentJson.get("db")) 
        cur  =  conn.cursor() 
        Plist = pd.read_sql("select * from Plist;", con=conn)
        df=pd.read_sql("select * from healthy_group28;", con=conn)
        click_log=pd.read_sql("select * from click_log;", con=conn)
    finally:
        if cur: cur.close() 
        if conn: conn.close()


    #如果没有点击过文章
    if len(click_log[click_log["lineID"]==user_ID])==0:
    #如果没有绑定病例码，random5篇：
        if len(Plist[Plist["lineID"]==user_ID]) == 0:
            NO=random.randint(0,(len(df.title)-5))
            article =  df[NO:(NO+5)].reset_index(drop=True)
            return(article_recommend_eval(article))

        #如果有绑定病例码，多个检查项目的话，就取最新的一条出来做推荐：
        if len(Plist[Plist["lineID"]==user_ID]) > 0:
            #把内外科等字去除
            article_key=Plist[Plist["lineID"]==user_ID].tail(1).reset_index(drop=True).POSkey[0].replace("外科","").replace("内科","").replace("科","")
            return(article_from_key(article_key,df))
        
    #如果有点击过文章
    if len(click_log[click_log["lineID"]==user_ID])>0:
        try:
            conn  =  pymysql.connect(host = secretFileContentJson.get("host"), user = secretFileContentJson.get("user"), passwd = secretFileContentJson.get("passwd"),db=secretFileContentJson.get("db")) 
            cur  =  conn.cursor() 
            sql="SELECT tag_g FROM click_log where lineID = '%s' order by time desc limit 1;" %user_ID 
            tag_g= pd.read_sql(sql, con=conn)

        finally:
            if cur: cur.close() 
            if conn: conn.close()
        article = recommend_five_article(tag_g["tag_g"].values[0]).reset_index(drop=True)
        return(article_recommend_eval(article))


# In[9]:


'''收到網頁的postback,就觸發確認是否打開文章, 同時將點選的文章存入click_log'''

import random
import datetime

def test_open_html(html,user_id):
    #將點選的文章存入click_log
    today=datetime.datetime.now()
    try:
        conn  =  pymysql.connect(host = secretFileContentJson.get("host"), user = secretFileContentJson.get("user"), passwd = secretFileContentJson.get("passwd"),db=secretFileContentJson.get("db")) 
        cur  =  conn.cursor() 
        data= pd.read_sql(("SELECT tag_g , KW FROM healthy_group28 where url = '%s';" %html), con=conn)
        cur.execute( "INSERT INTO click_log VALUES ('%s', '%s', '%s','%s',%s);" % (user_id,today,data.KW.values[0],html,data.tag_g.values[0])) 
        #注意有修改一定要commit
        conn.commit()
    finally:
        if cur: cur.close() 
        if conn: conn.close()

    return(TemplateSendMessage(
            alt_text="this is a confirm template",
            template=ConfirmTemplate(
                title='請確認是否開啟網頁',
                text='請確認是否開啟網頁',
                actions=[
                  {
                    "type": "uri",
                    "label": "是",
                    "uri": html
                  },
                  {
                    "type": "message",
                    "label": "否",
                    "text": "否"
                  }],)))


# In[10]:


'''help_article 做一個橋接的功能，把ask跟df一起帶入article_from_key '''

def help_article(ask):
    try:
        conn  =  pymysql.connect(host = secretFileContentJson.get("host"), user = secretFileContentJson.get("user"), passwd = secretFileContentJson.get("passwd"),db=secretFileContentJson.get("db")) 
        cur  =  conn.cursor() 
        df=pd.read_sql("select * from healthy_group28;", con=conn)
    finally:
        if cur: cur.close() 
        if conn: conn.close()
    #article_from_key(article_key,df)根據关键字搜寻出5篇文章
    return(article_from_key(ask,df))


# In[11]:


'''將Rich_manu綁定在用戶身上'''
'''Rich_manu 已經設置好並根據Rich_manu ID做轉場'''
def add_richmanu(user_id,rich_menu_id):
    linkRichMenuId=secretFileContentJson.get(rich_menu_id)
    linkMenuEndpoint='https://api.line.me/v2/bot/user/%s/richmenu/%s' % (user_id, linkRichMenuId)
    linkMenuRequestHeader={'Content-Type':'image/jpeg','Authorization':'Bearer %s' % secretFileContentJson["channel_access_token"]}
    lineLinkMenuResponse=requests.post(linkMenuEndpoint,headers=linkMenuRequestHeader)
    
'''
將菜單從用戶身上解除綁定，以後可能會用到
def del_richmanu(user_id):
    userMenuEndpoint='https://api.line.me/v2/bot/user/%s/richmenu' % (user_id)
    userMenuRequestHeader={'Authorization':'Bearer %s' % secretFileContentJson["channel_access_token"]}
    lineUnregisterUserMenuResponse=requests.delete(userMenuEndpoint,headers=userMenuRequestHeader)
'''


# In[12]:


'''
FollowEvent

1. 取得用戶個資，並存回伺服器
2. 把先前製作好的自定義菜單，與用戶做綁定
3. 回應用戶，歡迎用的文字消息與圖片消息

'''


# 載入Follow事件
from linebot.models.events import (
    FollowEvent
)

# 載入requests套件
import requests


# 告知handler，如果收到FollowEvent，則做下面的方法處理
@handler.add(FollowEvent)
def reply_text_and_get_user_profile(event):
    
    # 取出消息內User的資料
    user_profile = line_bot_api.get_profile(event.source.user_id)
        
     # 將用戶資訊存在檔案內
    with open("users.txt", "a") as myfile:
        myfile.write(json.dumps(vars(user_profile),sort_keys=True))
        myfile.write('\r\n')
        
    add_richmanu(event.source.user_id,"rich_menu_id")
    
    # 回覆文字消息與圖片消息
    line_bot_api.reply_message(
        event.reply_token,
        reply_message_new
    )


# In[13]:


'''解除綁定病患編碼'''
import pandas as pd
def delpno(user_id):
    try:
        conn  =  pymysql.connect(host = secretFileContentJson.get("host"), user = secretFileContentJson.get("user"), passwd = secretFileContentJson.get("passwd"),db=secretFileContentJson.get("db")) 
        cur  =  conn.cursor() 
        cur.execute( "UPDATE Plist SET lineID = '1' WHERE lineID = '%s';" % user_id) 
        #注意有修改一定要commit
        conn.commit()
    finally:
        if cur: cur.close() 
        if conn: conn.close()        
    return(TextSendMessage(text="病患編碼已解除綁定!請重新輸入新的病患編碼"))


# In[14]:


'''MessageEvent'''
from flask import Flask, request, abort
from linebot import *
from linebot.exceptions import *
from linebot.models import *
import pandas as pd
import re


#設置PNO的pattern, 判斷文字裡至少有6個的純數字
pattern=re.compile(r"^\d{6,}$")

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #添加PNO功能    
    if pattern.match(event.message.text):
        line_bot_api.reply_message(
        event.reply_token,
        ADDPNO(event.source.user_id,event.message.text))
    #使用者回復“否” 
    if event.message.text=="否":
         line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="謝謝,請通過下方圖文選單繼續操作"))
    #其他的輸入（關鍵字查詢文章）
    else:
        line_bot_api.reply_message(
            event.reply_token,
            help_article(event.message.text))


# In[15]:


'''PostbackEvent'''
import time

@handler.add(PostbackEvent)
def handle_post_message(event):
    #圖文選單功能,因為有部分function要用到使用者發來的message跟ID, 所以要寫在這裡, 不用function的功能就用字典引入
    if "::test::" in event.postback.data:
        if event.postback.data == "[::test::]重新綁定":
            line_bot_api.reply_message(
            event.reply_token,
            delpno(event.source.user_id))
        if event.postback.data == "[::test::]確認預約":
            line_bot_api.reply_message(
            event.reply_token,
            checkbooking(event.source.user_id))
        if event.postback.data =="[::test::]文章推薦":
            line_bot_api.reply_message(
            event.reply_token,
            article__recommend(event.source.user_id))
        if event.postback.data =="[::test::]協助就診":
            add_richmanu(event.source.user_id,"rich_menu_id_men1")
        if event.postback.data =="[::test::]返回首頁":
            add_richmanu(event.source.user_id,"rich_menu_id")
        #不會用到function的功能就用字典引入
        else:
            line_bot_api.reply_message(
            event.reply_token,
            template_message_dict.get(event.postback.data))
            add_richmanu(event.source.user_id,"rich_menu_id")
    #只要postback網頁，就存入click log
    if "https://" in event.postback.data:      
        line_bot_api.reply_message(
        event.reply_token,
        test_open_html(event.postback.data,event.source.user_id))


# In[16]:


'''line bot 的location功能，以後可以擴展使用'''
# @handler.add(MessageEvent, message=LocationMessage)
# def handle_message(event):
#     with open("location.txt", "a") as myfile:
#         myfile.write(event.source.user_id+","+str(event.message))
#         myfile.write('\r\n')


# In[17]:


if __name__ == "__main__":
    app.run(host='0.0.0.0' ,port=5000)


# In[ ]:




