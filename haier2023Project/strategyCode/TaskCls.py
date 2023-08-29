# -*- coding: utf-8 -*-
"""
Created on Sun Apr 23 11:48:35 2023

@author: chenyue
还有一种情况,就是对于某个账号如果请求够快,怎么根据异常的信息直接切换成另一个账号
    或者保险一些,就
"""
import requests
import logging
from logging import handlers
from datetime import datetime
import os
import json
from time import sleep
from threading import Thread
import warnings


def deprecate(func):
    def wrapper(*args, **kwargs):
        warnings.warn(f"{func.__name__} is deprecated.", DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)

    return wrapper


class CalcuTask:
    '''calcuName 用来定位需求中的模板
        rltDataPath 结果文件
        responsePath 响应文件
    '''
    rltDataPath = None
    responsePath = None
    postPath = None

    @classmethod
    def pathSet(cls, rltDataPath, responsePath, postPath):
        '''需要增加额外检验的分支'''
        cls.rltDataPath = rltDataPath
        cls.responsePath = responsePath
        cls.postPath = postPath

    def __init__(self, calcuName, calcuID):
        '''Name用来理解,一个用来对比和校验'''
        self.calcuName = calcuName
        self.calcuID = calcuID

    @staticmethod
    def realTimeCalcu_st(customModelStr, header):
        # 先把传来的Json保存到本地
        url = 'https://strategy.tmall.com/api/scapi'
        poyload = {
            'customModelStr': customModelStr,
            'contentType': "application/json",
            'path': "/api/v1/count/crowd/realtime",
            'withConditionGroup': 'true'
        }

        print('向策略中心api发送实时计算请求')
        return requests.post(url, json=poyload, headers=header, proxies={'https': None})

    @staticmethod
    def customDefCrowd_st(customModelStr, header):
        # 先把传来的Json保存到本地
        url = 'https://strategy.tmall.com/api/scapi'
        poyload = {
            'customModelStr': customModelStr,
            'contentType': "application/json",
            'path': "/api/v1/custom/strategy/group"
        }

        print('向策略中心api发送自定义人群请求')
        return requests.post(url, json=poyload, headers=header, proxies={'https': None})

    @staticmethod
    def customDefCrowd_db(customModelStr, header):
        # 先把传来的Json保存到本地
        url = 'https://databank.tmall.com/api/paasapi'
        poyload = {
            'customModelStr': customModelStr,
            'contentType': "application/json",
            'path': "/api/v1/custom/databank"
        }

        print('向数据银行api发送自定义人群请求')
        return requests.post(url, json=poyload, headers=header, proxies={'https': None})

    @staticmethod
    def preferAna(header, poyload):
        '''
        poyload 是字典形式,放在外部观察
        '''
        url = 'https://strategy.tmall.com/api/scapi'
        print('发送偏好分析请求')
        return requests.post(url, data=json.dumps(poyload), headers=header, proxies={'https': None})

    @classmethod
    def historyGet(cls):
        '''从本地的文件中获取,如果不存在直接返回空,后续步骤开始写数据'''
        if not os.path.exists(cls.responsePath):
            return []

        with open(cls.responsePath, 'r') as f:
            signList = []
            for _ in f.readlines():
                if _.strip():  # 最后空行跳过
                    # 把什么放入列表做标识有待讨论
                    # 姑且默认日志里的第二列就是唯一标识,不保险
                    # 第一列是日期时间
                    signList.append(_.split(',')[1])
        return signList

    def writeSomething(self, contentT, content):
        '''contentTlogInfo=response,result,post
            日志和结果要分开,因为不一定一次只传一个任务的结果
            写成实例方法还是类方法都行
            动态生成_temp文件'''
        if contentT == 'response':  # 历史检查的路径
            with open(self.responsePath, 'a') as f:
                tmStr = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write('%s,%s\n' % (tmStr, content))

        elif contentT == 'result':
            with open(self.rltDataPath, 'a') as f:
                f.write('%s\n' % content)

        elif contentT == 'post':
            with open(self.postPath, 'a') as f:
                f.write('%s\n' % content)

    def exceptHandle_join(self, response, ifDuplicate='', header={}, **kwargs):
        '''
        根据响应的内容影响主流程的效果
        kwargs
            产业 indus
            自动换头 autoswitch
        限流情况返回 wait关键字
        '''

        msg = response.text
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + msg)

        if msg.find('人群名称重复') != -1:
            print(kwargs)
            raise Exception('请检查参数信息')

        # 会有头分流的情况,通过关键字获取结果
        # 但是会出现中断,因为头分流的方法没有接收异常规则的位置
        # 还有情况是两个平台资源量都不够了
        if msg.find('用量不足') != -1:
            print(kwargs.get('header'), '\t资源量不足')  # 不设定也不会保存
            if kwargs.get('autoswitch'):
                return 'autoswitch'
            else:
                raise Exception('计算次数/资源量不足')

        if msg.find('类目未授权') != -1:
            # 基本是brand2会报
            print(kwargs.get('indus'))
            raise Exception('类目未授权,请更换使用的头变量')

        if msg.find('已过期') != -1:
            raise Exception('请刷新网页或重新使用账密登录')

        if msg.find('积极拒绝') != -1:
            print('由于目标计算机积极拒绝，无法连接')
            return 'wait'

        # 对于数银是问题,必须停,但策略中心用两个账号是有开出切换账号分支的可能的
        if msg.find('资源限流') != -1:
            print('资源限流,请稍后再试')
            return 'wait'

        if msg.find('477007033311') != -1:  # 特定问题
            print('请求太快')
            return 'wait'

        if msg.find('477001021005') != -1:
            # 找到说明重复,就往response路径中写入,下次中断再运行就会在主流程里跳过
            # 存在耦合,要统一标记形式
            self.writeSomething('response', ifDuplicate)
            return

        if msg.find('577001020000') != -1:
            raise Exception('请更换请求接口')

        if msg.find('人群人数过少') != -1:
            return

        if msg.find('SUCCESS') == -1:
            # 已经把post请求写入本地了,可以回看请求了什么
            raise Exception('请求失败,请检查平台或者请求命令')

        return True


class ExpMethod:

    @staticmethod
    def classic_db(CalcuTaskObj, templeJson, paraSeries, header, logTemple, filedStr, methodType='自定义人群',
                   internal=15):
        '''
        数银普遍的流程,返回字典
            人群序列化→保存报文→发送自定义圈人请求→报文异常解析→保存响应→抽取id→保存组合和id→等待→返回响应
            人群id 在dict['data']
        templeJson 组装好的人群模板
        paraSeries 参数序列,必须要有序号字段
        logTemple 日志模板
        filedStr 保留字段
        internal 每次请求时间间隔
        '''
        # 圈包必须用json方法
        crowdParaStr = json.dumps(templeJson, ensure_ascii=False)
        # 上传之前需要把post内容留档,一般不会回看
        CalcuTaskObj.writeSomething('post', '%s_%s,%s' % (CalcuTaskObj.calcuID, paraSeries['序号'], crowdParaStr))
        # api要先找一找
        r = CalcuTaskObj.customDefCrowd_db(crowdParaStr, header)
        # 统一处理异常情况,同时会在控制台打印响应
        CalcuTaskObj.exceptHandle_join(r, ifDuplicate='%s,%s' % (logTemple, r.text))
        # 记录日志并等待
        CalcuTaskObj.writeSomething('response', '%s,%s' % (logTemple, r.text))
        # P9,P10保留包名的方法配置舍弃掉,这是当时向书童不保留人群ID的妥协产物
        crowdId = json.loads(r.text)['data']
        CalcuTaskObj.writeSomething('result', '%s,%s,%s' % (logTemple, filedStr, crowdId))
        # 先输出再等待
        sleep(internal)
        return json.loads(r.text)
