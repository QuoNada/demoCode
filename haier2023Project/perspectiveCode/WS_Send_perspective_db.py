'''
先用测试表读写数据
需要把删除数据的方法改掉,先在brand3的数银画像上测试
ID和店铺相绑定,可从本地中间txt读,可能idSeries 没必要准备
如果不用列表,遇到中断的情况还要做个检查
'''
from os import path
repoPath = path.dirname(path.dirname(path.dirname(__file__)))
import sys

sys.path.append(repoPath)  # 项目目录
from PECHOINProject.clsPack.Web_Interact import WebQuery
from haier2023Project.Result.Header.HeaderGet import header_get, brandMap

from WSDataBank import PerspectiveWS, DataStore  # 同一路径
import websocket
from datetime import datetime
from tagMap_v3 import tagList_db
import os
import re

# 准备头
headerH = header_get('brand1', '数据银行')  # 3个位置用,单id_详情查询,单id_condtion查询,websocketAPP参数
headerC = header_get('brand2', '数据银行')
rltDataPath = path.join(repoPath,r"haier2023Project\Result\Data\middleData_7月\id_p5 - 副本.txt")


if __name__ == '__main__':

    # 定义数据库存储位置
    dstore = DataStore(os.path.join(repoPath, 'haier2023Project/perspectiveCode/haier_portrait.db'),
                       'haier2023_report0517', prdOnly=True)

    # 读取本地id
    with open(rltDataPath, 'r') as f:
        while True:
            infoSeires = f.readline()
            if not infoSeires:  # 最后一行结束循环,不能把空带到查询里
                break

            crdIdMath = re.search(r'\b6\d{7}\b', infoSeires)  # 默认是8位数字,6开头,能避开日期标识
            crdId = crdIdMath.group()
            localCnt = dstore.queryData_equal(crdId)
            if localCnt:  # 如果数据库已经有了就跳过
                continue

            if infoSeires.find('brand1') != -1:  # 头分流
                header = headerH
                accName = 'brand1'
            elif infoSeires.find('brand2') != -1:
                header = headerC
                accName = 'brand2'

            wq = WebQuery(header, '数据银行')  # 实例化网页交互对象
            infoDict = wq.singleIdQuery_detail(crdId)  # 从网页端获取包名,以后可以从人群数据库里获取,更快

            # 有人群包看不了的情况,可能是人数小于两千,也可能是计算失败被人为的删了
            if not infoDict.get('data') \
                    or not infoDict.get('data')['count'] \
                    or str(infoDict).find('你没有权限使用这个资源') != -1 \
                    or str(infoDict).find('您无法查看人群详情') != -1:
                print(crdId + '无效或小于2000\t' + str(infoDict))

                if str(infoDict).find('Missing smartId') != -1:  # 估计是过期了
                    sys.exit()
                continue  # 不往下走

            # 定义部分要写入数据库的数据
            dataMap = {'modify_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                       'login_account': brandMap[accName]['account'],  # 暂时依赖保存登录信息的脚本
                       'crowd_id': crdId,
                       'crow_name': infoDict['data']['crowdName']  # 先不用到人数
                       }

            # 定义含app方法的对象
            dsend = PerspectiveWS(header, crdId, tagList=tagList_db)  # 试一试用不同的关键字

            # 实例化app对象
            ws = websocket.WebSocketApp("wss://ws-insight-engine.tmall.com/",  # 数银和策略中心是同一个握手地址
                                        # 用位置传参不保险,不知道app对象会怎么调用的lambda函数
                                        on_message=lambda ws, message: dstore.on_message_test(ws, message,
                                                                                         fieldDict=dataMap),
                                        on_error=dsend.on_error,
                                        on_close=dstore.on_close,
                                        header=header
                                        )

            ws.on_open = dsend.on_open_db_crowdPerspective  # 只传方法
            ws.run_forever()
