'''
先用测试表读写数据
pycharm对跨项目引用不太友好,需要把项目空间也改掉
不同的报告也应该区分挂件内容
brand1项目p6需求不用头分流
'''
from os import path

repoPath = path.dirname(path.dirname(path.dirname(__file__)))  # 定义项目路径
import sys

sys.path.append(repoPath)  # 项目目录

from PECHOINProject.clsPack.Web_Interact import WebQuery
from haier2023Project.Result.Header.HeaderGet import header_get, brandMap
from haier2023Project.perspectiveCode.WSDataBank import DataStore, ReportWS
import websocket
from datetime import datetime

plt = '策略中心'
brandName = 'brand3'

crdId = 66056721  # 哪怕不知道包名,去数据库看结果就能知道

if __name__ == '__main__':
    templeFile = path.join(repoPath, 'haier2023Project/prefer_corrReportCode/reportTemple_st.json')  # 品类偏好分析只依赖reportid
    header = header_get(brandName, plt)
    wq = WebQuery(header, plt)  # 实例化网页交互对象获取报告id

    infoDict = wq.singleReportGet_st('相关性分析', crdId)  # 上面可以插入列表/文件行循环

    # 哪怕包没建过,依然是返回success
    if not infoDict.get('data'):
        print(crdId + '无效的人群id\t' + str(infoDict))
        sys.exit()
    else:
        reportId = infoDict['data'][0]['reportId']
        crdInfoDict=wq.singleIdQuery_detail(crdId)

    for bi_widget_name in ['一级类目购买偏好', '叶子类目购买偏好']: # 相关性分析基本就这两项
        # 定义部分要写入数据库的数据
        dataMap = {'modify_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                   'login_account': brandMap[brandName]['account'],  # 暂时依赖保存登录信息的脚本
                   'crowd_id': crdId,
                   'crow_name': crdInfoDict['data']['crowdName'],  # 相关性分析不能用报告的接口获取人群包名
                   'bi_widget_name': bi_widget_name
                   }

        # 定义含app方法的对象
        dsend = ReportWS(header, crdId, reportId=reportId, widgetName=bi_widget_name, templePath=templeFile)

        dstore = DataStore(path.join(repoPath, 'haier2023Project/perspectiveCode/haier_portrait.db'),
                           'haier2023_report0515')
        # 实例化app对象
        ws = websocket.WebSocketApp("wss://ws-insight-engine.tmall.com/",  # 数银和策略中心是同一个握手地址
                                    on_message=lambda ws, message: dstore.on_message(ws, message, fieldDict=dataMap),
                                    on_error=dsend.on_error,
                                    on_close=dstore.on_close,
                                    header=header
                                    )

        ws.on_open = dsend.on_open_corr  # 只传方法
        ws.run_forever()
