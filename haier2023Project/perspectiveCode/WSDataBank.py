# -*- coding: utf-8 -*-
"""
Created on Thu May 11 15:08:14 2023

@author: chenyue
不直接跨项目引用类
关键的映射放在构建处
"""
import os
import base64
import threading
import time
from datetime import datetime, timedelta
import requests
import sqlite3
import json
import warnings
from tagMap_v3 import tagMap_db_all, tagMap_st_casarte

# 品类偏好分析方法用到
widgetIDs = {
    # 品类偏好报告
    '产品偏好分析': 890025,
    '商品标题关键词': 890050,
    '品牌偏好分析': 890080,
    '商品偏好分析': 890095,
    # 相关性分析报告
    '叶子类目购买偏好': 812735,
    '一级类目购买偏好': 812731,
    '品牌购买偏好': 812739
}


def deprecate(func):
    def wrapper(*args, **kwargs):
        warnings.warn(f"{func.__name__} is deprecated.", DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)

    return wrapper


class WSBase:
    def __init__(self, header, crowdId):
        '''
        reportType挂件名字,str
        '''
        self.crowdId = crowdId
        self.header = header

        self._headerFill()  # 每次实例化都产生随机值

    def _headerFill(self):
        '''补充一些关键字再试试'''

        self.header['Upgrade'] = 'websocket'
        self.header['Sec-WebSocket-Version'] = '13'
        self.header['sec_websocket_key'] = base64.b64encode(os.urandom(16)).decode('utf-8').strip()
        self.header['Cache-Control'] = 'no-cache'

    @staticmethod
    def on_error(ws, error):
        # Handle errors here
        print('error message:%s\n' % error)


class PerspectiveWS(WSBase):

    def __init__(self, header, crowdId, tagList=[]):
        '''
        透视需要传入标签相关列表
        tagList是中文形式标签列表
        '''
        super().__init__(header, crowdId)
        self.tagList = tagList

    def _getCondition(self):
        '''不让类外用'''
        path = 'https://databank.tmall.com/api/ecapi'
        # 3级组装
        tmp = {
            "bizType": "CUSTOM_ANALYSIS",
            "paramsMap": {
                "DATE": (datetime.now() - timedelta(1)).date().strftime('%Y-%m-%d %H:%M:%S'),  # 默认是T-1
                "CROWD_ID": self.crowdId
            }
        }
        # 2级组装
        data = {
            'contentType': 'application/json',
            'path': '/v1/crowd/perspective/build/param',
            'perspectiveParamStr': json.dumps(tmp)
        }
        res = requests.post(url=path, headers=self.header, json=data)

        self.condition = str(json.loads(res.text)['data'])

    def _getWsUpload_db(self):
        # rid应该和方法连用
        rid = str(round(time.time() * 1000000))[:15]
        # 映射需要提前准备好
        tagListEn = [tagMap_db_all['tagMap_zhk'][_] for _ in self.tagList]

        sendJson = {
            "method": "/iSheetCrowdService/report",
            "headers": {
                "rid": rid,
                "type": "PULL"
            },
            "body": {
                "args": {
                    "id": "287",  # 估计是报告的版本? 可以从ws中拿到
                    "condition": self.condition,
                    "tags": tagListEn,
                    "bizParam": {
                        "databankCrowdId": self.crowdId,  # 变量
                        "bizType": "CUSTOM_ANALYSIS",
                        "tag_identifier": "all",
                    },
                    "insightType": 0,
                    "interaction": True,
                    "rateParam": {},
                    "appId": "208"
                }
            }
        }
        self.sendJson = sendJson

    def on_open_db_crowdPerspective(self, ws):
        '''没有使用函数高阶化的工具'''
        self._getCondition()
        self._getWsUpload_db()
        ws.send(json.dumps(self.sendJson))

    def _getWsUpload_st(self):
        '''策略中心 人群透视'''

        rid = str(round(time.time() * 1000000))[:15]
        tagListEn = [tagMap_st_casarte['tagMap_zhk'][_] for _ in self.tagList]  # 不能用数银的映射
        sendJson = {
            "method": "/iSheetCrowdService/offline",
            "headers": {
                "rid": rid,
                "type": "PULL"
            },
            "body": {
                "args": {
                    "id": "661",
                    "perspectTaskId": self.crowdId,
                    "bizParam": {
                        "crowdIds": [
                            self.crowdId
                        ],
                        "tagList": tagListEn
                    },
                    "appId": "209"
                }
            }
        }
        self.sendJson = sendJson

    def on_open_st_crowdPerspective(self, ws):
        '''方法与平台一一对应,策略中心不需要conditon'''
        self._getWsUpload_st()
        ws.send(json.dumps(self.sendJson))


class ReportWS(WSBase):

    def __init__(self, header, crowdId, reportId=0, widgetName='', templePath=''):
        '''
        widgetId 没办法在顶层传入,还需要新建映射
        '''
        super().__init__(header, crowdId)
        self.reportId = reportId
        self.widgetId = widgetIDs[widgetName]
        self.templePath = templePath

    def _getWsUpload_catePerfer_st(self, referer):
        '''
        需要写初始化的时候对应的挂件名称
        还在测试,自己拼或者直接从网页上拿,需要预先指定模板位置
        先暂时用着品类偏好分析的名字,等报告多了再
        '''
        rid = str(round(time.time() * 1000000))

        with open(self.templePath, 'r') as f:
            sendJson = json.load(f)

        sendJson['headers']['rid'] = rid
        sendJson['body']['args']['referer'] = referer
        sendJson['body']['args']['id'] = self.widgetId
        # 模板只保留了一种维度 同样是一种耦合
        sendJson['body']['args']['selections'][0]['showText'] = self.reportId
        sendJson['body']['args']['selections'][0]['restrictList'][0]['value'] = self.reportId
        sendJson['body']['args']['selections'][0]['eq'][0]['value'] = self.reportId

        self.sendJson = sendJson

    def on_open_catePerfer(self, ws):
        self._getWsUpload_catePerfer_st('strategy-categoryPreferenceAnalysis')  # open方法没有传参的地方
        ws.send(json.dumps(self.sendJson))

    def on_open_corr(self, ws):
        '''和品类偏好分析一个模式'''
        self._getWsUpload_catePerfer_st('strategy-correlationAnalysis')
        ws.send(json.dumps(self.sendJson))


class DataStore:
    '''数据库的读写'''

    def __init__(self, dbPath, tableName, prdOnly=False):
        # 先保险着来,cur跟着实例走
        self.dbPath = dbPath
        self.tableName = tableName
        self.prdOnly = prdOnly

    def queryData_equal(self, crowd_id):
        '''
        检查有无某个id,没有return就是0
        不知道为啥突然反馈sql问题,然后又正常了
        '''
        sqlStr = 'SELECT count(*) from {tableName} WHERE crowd_id = {crowd_id}'.format(
            tableName=self.tableName,
            crowd_id=crowd_id
        )

        cnn = sqlite3.connect(self.dbPath)  # 可以变为类方法,共用一个连接
        cur = cnn.cursor()  # 建立公用的连接
        res = cur.execute(sqlStr)
        return res.fetchone()[0]

    def queryData_inTuple(self, idTuple,**kwargs):
        '''
        用到in语句传入括起来的id元组
        返回列表格式数据
        kwargs filedName:data 等值查询
        '''
        
        sqlStr='''select * from {tbName} where crowd_id in {idTuple}'''.format(
            tbName=self.tableName,
            idTuple=str(idTuple))
        
        # 增加更多的条件
        if kwargs:
            for k,v in kwargs.items():
                sqlStr += ' and %s = "%s"'%(k,v) 
        
        cnn = sqlite3.connect(self.dbPath)
        cur = cnn.cursor()
        # 只查询一次
        res = cur.execute(sqlStr)
        data = [r for r in res]
        cnn.close()
        return data  # 返回列表,在主流程里转数据帧

    def insertData(self, msg, modeList=['dev'], **kwargs):
        '''
        每一条数据都要connect,略麻烦
        按位传递,所有字段都是必要的
        modeList prd,dev 生产/开发
        '''
        kwargs['data'] = msg
        filed = tuple(kwargs.keys())
        value = tuple(kwargs.values())
        sqlStr = "INSERT INTO {tableName} {colTuple} VALUES {valueTuple}".format(
            tableName=self.tableName,
            colTuple=str(filed),
            valueTuple=str(value),
        )

        cnn = sqlite3.connect(self.dbPath)  # 可以变为类方法,共用一个连接
        cur = cnn.cursor()  # 建立公用的连接
        # cur.executescript(sqlStr + ';' + sqlStr.replace(self.tableName,self.tableName+'_full')) #运行多个sql语句
        if 'prd' in modeList:
            cur.execute(sqlStr)  # 往生产表写
            cnn.commit()
            print('生产表写入')

        if 'dev' in modeList:
            cur.execute(sqlStr.replace(self.tableName, self.tableName + '_full'))
            cnn.commit()
            print('测试表写入')

        cnn.close()

    def _timerClose(self, ws):
        '''
        显式关闭连接,不需要ws对象外的任何参数
        '''
        self.t_close = threading.Timer(15, ws.close)  # 关闭了才能进入下一id/标签循环
        self.t_close.start()

    # 之前放在on_close里,发现太慢;用ws.close()是快,但调不起来on_close;所以要在其他地方从新组合关闭和写数据的流程
    def _timerPrd(self, msg, **kwargs):
        '''
        生产表写数据
        '''
        self.t_prd = threading.Timer(10, self.insertData, args=(msg, ['prd']), kwargs=kwargs)
        self.t_prd.start()

    def on_message(self, ws, message, fieldDict):
        '''
        crowd_id 如果不删除就用不着
        fieldDict 的modify_time键基本是同一时间,不针对写入时间再做拆分
        #消息的结果数据,message是string格式
        '''
        print(message)  # 无论正常/异常消息都会打印

        if hasattr(self, 't_close') and hasattr(self, 't_prd'):  # 如果有计时器就先取消,等最新的消息处理完,不隐藏变量有被篡改的风险
            self.t_close.cancel()
            self.t_prd.cancel()

        # 系统错误或者数据是空的直接退出,但不一定,还能需要等地
        if message.find('用量不足') != -1:
            ws.close()  # 不属于正常关闭,但这些问题没必要往下走,不仅时被调用者不继续,主流程的循环也应该关闭
            raise Exception(message)

        # 不能关的太早!否则拿到的都是缓存数据
        # 尽量不做数据库删除操作
        if message.find('NO_SELECTION_PARAM') == -1 and message.find('error') == -1:  # 没有错误信息才能往操作数据库
            if not self.prdOnly:  # 不指定生产环境唯一,就在测试表也写入数据
                self.insertData(message, modeList=['dev'], **fieldDict)  # 默认测试环境
            self._timerPrd(msg=message, **fieldDict)  # 10秒后会往正式表里写数据,不是最后一次都会被取消
            # AI回答:放if分之外调用多次,但只有第一次生效
            # NUM_LESS_300可以不处理,个别包的慢一两分钟问题不大
            self._timerClose(ws)  # 15秒后会关闭连接,进入下一个datasend对象=下一个ws对象

    def on_close(self, ws, close_status_code, close_msg):
        '''
        close_status_code,close_msg全都是None
        和ws.close()不一样
        '''
        # 关闭前保存最后一次的结果
        print("Connection closed\n")  # 需要走到这一步,而不能是报错
