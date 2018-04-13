# encoding = utf-8
from tkinter import *
from tkinter.filedialog import *
import tkinter.messagebox
import psutil
import sys
import os
import requests
import ctypes
import re
import urllib
import time
import threading
import _thread
from bs4 import BeautifulSoup
import sys
import re
import codecs
import os
import shutil
import jieba
# 添加停用词
import jieba.analyse
import string
import math

req_header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Cache-Control': 'max-age=0',
    'Cookie': 'UM_distinctid=15f056a32d60-092012e87233a9-37624605-100200-15f056a32d732e; bdshare_firstime=1507624368490; PPad_id_PP=1; bookid=2; chapterid=29; chaptername=%25u7B2C%25u4E8C%25u5341%25u516B%25u7AE0%2520%25u6253%25u72D7%25u68D2%25u6CD5; bcolor=; font=; size=; fontcolor=; width=; CNZZDATA1261736110=1709889067-1507619242-null%7C1507624745; Hm_lvt_5ee23c2731c7127c7ad800272fdd85ba=1507624367,1507624831; Hm_lpvt_5ee23c2731c7127c7ad800272fdd85ba=1507624896',
    'Host': 'www.qu.la',
    'Proxy-Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'

}
req_url_base = 'http://www.qu.la/book/'
pid_thread = 0
# 纪录控件状态
stateDelWord = 0
statePart = 0
stateCount = 0
stateMerge = 0
stateCalBack = 0


class Application():
    # 定义做界面的类
    root = Tk()

    BookNum = "2"
    fileName1 = " "
    fileName2 = " "
    # 添加滚动条
    scrollbar = Scrollbar(root)
    # 创建列表
    listbox = Listbox(root, )
    listbox.grid(row=1, column=0, columnspan=5, rowspan=90, sticky=S + N + W + E)

    def __init__(self, width=720, height=420):
        self.w = width
        self.h = height
        self.stat = True
        self.staIco = None
        self.stoIco = None

    def center(self):
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = int((ws / 2) - (self.w / 2))
        y = int((hs / 2) - (self.h / 2))
        self.root.geometry('{}x{}+{}+{}'.format(self.w, self.h, x, y))

    def GridBtn(self):
        # 创建按钮
        self.btnSpider = Button(self.root, command=self.eventSpiders, width=19, height=3)
        self.btnSpider.grid(row=0, column=0)
        self.btnDelWord = Button(self.root, text="删除通用词", command=self.eventDelWord, width=19, height=3)
        self.btnDelWord.grid(row=0, column=1)
        self.btnPart = Button(self.root, text="分词化", command=self.eventPart, width=19, height=3)
        self.btnPart.grid(row=0, column=2)
        self.btnContrast = Button(self.root, text="对比文档相似度", command=self.eventMarge, width=19, height=3)
        self.btnContrast.grid(row=0, column=3)
        self.btnQuit = Button(self.root, text="退出程序", command=self.root.quit, width=19, height=3)
        self.btnQuit.grid(row=0, column=4)

    def eventSpiders(self):
        if self.stat:  # 判断当前看控件的状态
            if self.get_section_stop():
                self.btnSpider["text"] = "启动爬虫"
                self.stat = False
        else:
            # 启动线程

            _thread.start_new_thread(self.get_section_txt, (1,))
            self.stat = True
        self.btnSpider["state"] = "active"

    def eventDelWord(self):
        if self.stat:  # 判断当前看控件的状态
            if self.get_section_stop():
                self.stat = False
        else:
            # 启动线程
            try:
                _thread.start_new_thread(self.read_file_CD, (2,))
            except:
                self.listbox.insert(END, "线程启动失败!")
            self.stat = True
        self.btnDelWord["state"] = "active"

    def eventPart(self):
        if self.stat:  # 判断当前看控件的状态
            if self.get_section_stop():
                self.stat = False
        else:
            # 启动线程
            try:
                _thread.start_new_thread(self.read_file_cut, (3,))
            except:
                self.listbox.insert(END, "线程启动失败!")
            self.stat = True
        self.btnPart["state"] = "active"

    def eventMarge(self):
        if self.stat:  # 判断当前看控件的状态
            if self.get_section_stop():
                self.stat = False
        else:
            stateSelect1 = self.SelectWin1()
            stateSelect2 = self.SelectWin2()
            # _thread.start_new_thread(self.SelectWin, (4,))
            # 启动线程
            if stateSelect1 and stateSelect2:
                try:
                    _thread.start_new_thread(self.merge_key, (5,))
                except:
                    self.listbox.insert(END, "线程启动失败!")
            self.stat = True
        self.btnPart["state"] = "active"

    def loop(self):
        # 禁止改变窗口的大小
        self.root.resizable(False, False)  # 禁止修改窗口大小
        # 控件按钮
        self.GridBtn()
        self.center()
        self.eventSpiders()
        # 判断当前的控件状态 确保只有
        if stateDelWord == 1:
            self.eventDelWord()
        if statePart == 1:
            self.eventPart()
        if stateMerge == 1:
            self.eventMarge()
        self.root.mainloop()

    # ===========================================================================================================
    # -----------------------------------------------网络爬虫----------------------------------------------------
    # 建立字典 存储信息
    def get_section_txt(self, value):

        self.listbox.delete(0, END)
        path = "resChese\\res\\原文\\"  # 小说存取目录
        num = 1  # 记录章节数字编号
        txt = {}
        txt['id'] = "1"
        # 小说名字
        txt['title'] = ''
        # 小说地址
        req_url = req_url_base + txt['id'] + '/'
        # 连接地址
        res = requests.get(req_url, params=req_header)
        # soup转换
        soup = BeautifulSoup(res.text, 'html.parser')
        # 获取小说题目
        txt['title'] = soup.select('#wrapper .box_con #maininfo #info h1')[0].text
        # 获取作者
        txt['auther'] = soup.select('#wrapper .box_con #maininfo #info p')[0].text
        # 获取最新更新时间
        txt['time'] = soup.select('#wrapper .box_con #maininfo #info p')[2].text
        # 最新更新章节
        txt['new_section'] = soup.select('#wrapper .box_con #maininfo #info p')[3].text
        # 获取小说简介
        txt['intro_section'] = soup.select('#wrapper .box_con #maininfo #intro')[0].text.strip()
        # print('编号:'+'{0:0>8}'.format(str(txt['id'])) + '   小说名:《' + str(txt['title']) +'》 开始下载')
        begin_iterm = '编号:' + '{0:0>8}'.format(str(txt['id'])) + '   小说名:《' + str(txt['title']) + '》 开始下载'

        self.listbox.insert(END, begin_iterm)
        # 获取所有章节的总数

        self.listbox.insert(END, "正在寻找第一章页面内容")
        all_page = soup.select("#wrapper .box_con #list dl dd a")
        # 获取总的章数页面
        all_page_num = len(all_page)
        # 获取第一章页面的连接
        first_page = all_page[0]['href'].split('/')[3]
        # 打开文件将相关信息写入文件
        fo = open(path + '{0:0>8}-{1}.txt'.format(txt['id'], txt['title']), 'ab+')
        fo.write((txt['title'] + '\r\n').encode('UTF-8'))
        fo.write((txt['auther'] + '\r\n').encode('UTF-8'))
        fo.write((str(all_page_num) + '\r\n').encode('UTF-8'))
        fo.write((txt['time']).encode('UTF-8'))
        fo.write(('\n************内容***********\r\n').encode('UTF-8'))
        fo.write(('\t' + txt['intro_section'] + '\r\n').encode('UTF-8'))
        # 关闭文件
        fo.close()
        # 进入循环 写入每章内容
        while (1):
            try:
                # 请求当前章节页面
                current_section = requests.get(req_url + str(first_page), params=req_header)
                # soup转换
                soup = BeautifulSoup(current_section.text, 'html.parser')
                # 获取章节名称
                section_name = soup.select('#wrapper .content_read  .box_con .bookname h1')[0].text
                # 获取章节内容
                section_text = soup.select('#wrapper .content_read  .box_con #content')[0].text
                # 将文本中无关的项去掉
                # 按照指定格式替换章节内容，运用正则表达式
                section_text = re.sub('\s+', '\r\n\t', section_text).strip('\r\n')
                # 获取下一章连接
                first_page = soup.select('#wrapper .content_read  .box_con .bottem2 a')[2]['href']
                # 判断退出条件
                if (first_page == './'):
                    finish_text = txt['title'] + '所有章节下载完毕'
                    self.listbox.insert(END, finish_text)
                    break
                # 打开文件 将小说内容写入文本
                # fo_section = open(path + '{0:0>8}.txt'.format(section_name), 'ab+')
                fo_section = open(path + str(num) + '.txt', 'ab+')  # 为了后期好处理 将章节名称改为数字编号
                fo_section.write((section_name + '\r\n').encode('UTF-8'))
                # 将当前章节的内容写入
                fo_section.write(('\t' + str(section_text) + '\r\n').encode('UTF-8'))
                iterm = '{0:0>8}.txt'.format(section_name)
                self.listbox.insert(END, iterm)
                # 关闭文件
                fo_section.close()
                num = num + 1
                # print(section_text)
            except:
                self.listbox.insert(END, str(section_name + "读取出错"))
        self.listbox.insert(END, "所有文档下载完毕!")
        return True

    # --------------------------------------------------- 删除停用词----------------------------------------

    # 定义函数 读取文件 删除停用词
    def read_file_CD(self, value):
        # 每次执行操作前将listbox清空
        self.listbox.delete(0, END)
        # 定义文件的路径
        # 原文件所在路径
        path = "resChese\\res\\原文\\"
        # 停用词所在文件路径
        stop_path = "resChese\\res\\停用词\\停用词\\"
        # 删除停用词后文件路径后文件存储路径
        respath = "resChese\\res\\停用词\\res\\"
        num = 1
        # 加载通用词
        stop_file_C = stop_path + '中文停用词.txt'
        print(stop_file_C)
        stop_word_fo = open(stop_file_C, 'r')  # 返回文件的对象
        stop_word = stop_word_fo.read()  # 获取通用词
        result_str = ""
        while num < 500:
            source_file_C = path + str(num) + ".txt"
            source_fo = open(source_file_C, 'r', encoding='UTF-8')
            # 读取内容
            source_str = source_fo.readline()
            source_str = source_str.rsplit('\n')
            result_file_CD = respath + str(num) + "_D.txt"
            self.listbox.insert(END, str(num) + ".txt 处理完成")
            # 打开目标文件 向目标文件中写入
            result_fo = open(result_file_CD, 'ab+')
            while source_str:
                for source_seg in source_str:
                    if source_seg not in stop_word:
                        result_str += source_seg
                source_str = source_fo.readline()
                result_fo.write((result_str + "\n").encode('UTF-8'))
                result_str = " "
            num = num + 1  # 处理文档数量加1
        self.listbox.insert(END, "所有文档删除停用词完成!")
        return TRUE

    # --------------------------------------------------------分词------------------------------------------------
    # 定义函数 读取文件
    def read_file_cut(self, value):
        self.listbox.delete(0, END)
        # 定义文件的路径
        path = "resChese\\res\\停用词\\res\\"
        respath = "resChese\\res\\分词化\\"
        num = 1
        while num < 500:  # 处理500个中文文档
            name = num
            file_name = path + str(name) + "_D.txt"
            res_name = respath + str(name) + "_C" + ".txt"
            source_fo = open(file_name, "r", encoding='UTF-8')
            self.listbox.insert(END, str(num) + ".txt 分词完成!")
            # 打开文件读取数据
            result_fo = codecs.open(res_name, 'ab+', encoding='UTF-8')
            source_line = source_fo.readline()
            source_line = source_line.rstrip('\n')
            while source_line:
                seg_line = jieba.cut_for_search(source_line)
                output_line = ' '.join(seg_line)
                # 写入文件
                result_fo.write(output_line + '\n')
                source_line = source_fo.readline()  # 循环读取文件
            num = num + 1
        source_fo.close()
        result_fo.close()
        self.listbox.insert(END, "所有文件分词完成!")
        return TRUE

    # --------------------------------------统计函数---------------------------------------------

    def count_word(self, file_name):

        # 定义文件的路径
        path = "resChese\\res\\分词化\\"
        res_path = "resChese\\res\\统计\\"
        # 文件的名称
        num = 3
        source_file_name = file_name
        # source_file_name = path + str(file_name) + "_C.txt"
        res_file_name = res_path + str(num) + "_CC.txt"
        # 统计关键词的个数
        # 计算机文件的行数
        line_nums = len(open(source_file_name, 'r', encoding='UTF-8').readline())

        # self.listbox.insert(END,"文件的行数:"+str(line_nums))
        # 统计格式是<key:value><属性:出现个数>
        i = 0
        # 定义字典 决定了统计的格式
        table = {}
        source_fo = open(source_file_name, "r", encoding='UTF-8')
        result_fo = open(res_file_name, "w")
        while i < line_nums:
            source_line = source_fo.readline()
            # source_line = source_line.rsplit("\n")

            # 将读取的字符用空格分割开
            words = str(source_line).split(" ")
            # 字典的插入与赋值
            for word in words:
                if word != " " and word != "\n" and word != "\t" and word in table:
                    num = table[word]
                    table[word] = num + 1
                elif word != "":  # 如果单词之前没有出现过
                    table[word] = 1
            i = i + 1
        # 将统计的键值排序
        dic = sorted(table.items(), key=lambda asd: asd[1], reverse=True)
        for i in range(len(dic)):
            # print("key = %s,value = %s",dic[i][0],dic[i][1])
            result_fo.write("<" + dic[i][0] + ":" + str(dic[i][1]) + ">\n")
        # self.listbox.insert(END,dic)
        return dic  # 函数返回值
        source_fo.close()
        result_fo.close()

    # ------------------------------------------计算余玄值----------------------------
    def a(self):
        print(self.var1.get())

    def merge_key(self, value):
        # 清空libox里面的内容
        # num1 = input("请输入第一个文档的编号:")
        # num2 = input("请输入第二个文档的编号:")
        # self.listbox.delete(0,END)
        dic1 = []
        dic2 = []
        dic1 = self.count_word(self.fileName1)
        dic2 = self.count_word(self.fileName2)

        # 合并关键字
        array_key = []
        # 将文件1中的关键字添加到数组中去
        for i in range(len(dic1)):
            array_key.append(dic1[i][0])
        # 将文件2中的关键字添加到数组中去
        for i in range(len(dic2)):
            if dic2[i][0] not in array_key:  # 关键字在数组中已经出现过
                array_key.append(dic2[i][0])

        # 计算词频
        array_num1 = [0] * len(array_key)
        array_num2 = [0] * len(array_key)
        for i in range(len(dic1)):
            key = dic1[i][0]
            value = dic1[i][1]
            j = 0
            while j < len(array_key):
                if key == array_key[j]:
                    array_num1[j] = value
                    break
                else:
                    j = j + 1
        for i in range(len(dic2)):
            key = dic2[i][0]
            value = dic2[i][1]
            j = 0
            while j < len(array_key):
                if key == array_key[j]:
                    array_num2[j] = value
                    break
                else:
                    j = j + 1

        # 计算两个向量的点积
        x = 0
        i = 0
        while i < len(array_key):
            x = x + array_num1[i] * array_num2[i]
            i = i + 1

        # 计算两个向量的模
        i = 0
        sq1 = 0
        while i < len(array_key):
            sq1 = sq1 + array_num1[i] * array_num1[i]
            i = i + 1
        i = 0
        sq2 = 0
        while i < len(array_key):
            sq2 = sq2 + array_num2[i] * array_num2[i]
            i = i + 1
        try:
            result = float(x) / (math.sqrt(sq1) * math.sqrt(sq2))
        except:
            self.listbox.insert(END, "除数不能为零！")
        resultFloat = result
        #resultStr = "文档"+num1+"和"+ num2+"的相似度是:"+str(resultFloat)+"%"
        #创建新的窗口
        showRoot = Tk()
        label = Label(showRoot,text = "相似度:"+str(resultFloat),height = 7,width = 25)
        label.grid(row = 0)
        showRoot.mainloop()
        print(resultFloat)
        return TRUE

    def SelectWin1(self):
        fd = LoadFileDialog(self.root)  # 创建打开文件对话框
        self.fileName1 = fd.go()  # 显示打开文件对话框，并获取选择的文件名称
        return True

    def SelectWin2(self):
        fd = LoadFileDialog(self.root)  # 创建打开文件对话框
        self.fileName2 = fd.go()  # 显示打开文件对话框，并获取选择的文件名称
        return True

    #---------------------------------------------------------停止----------------------------------------------
    def get_section_stop(self):

        return True


if __name__ == "__main__":
    w = Application()  # 创建对象并传递绑定的函数
    w.loop()
