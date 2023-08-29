# -*- coding: utf-8 -*-
"""
Created on Tue Feb 14 15:03:29 2023

@author: chenyue

"""
import json, requests
from time import sleep

#策略中心的quota接口是个特殊的paasapi
urlMap={
        '策略中心':{
            'quota':'https://strategy.tmall.com/api/paasapi?&path=/api/v1/score/packageList',
            'crowdList':'https://strategy.tmall.com/api/scapi?path=/api/v1/custom/list',
            'delCrowd':'https://strategy.tmall.com/api/scapi',
            'delPath':"/api/v1/custom/deleteCrowds",
            'idDetail':'https://strategy.tmall.com/api/scapi?path=/api/v1/custom',
            'idCnt':'https://strategy.tmall.com/api/scapi?path=/api/v1/custom/getCrowd'
            },
        '数据银行':{
            'quota':'https://databank.tmall.com/api/paasapi?path=/api/v1/score/packageList',
            'crowdList':'https://databank.tmall.com/api/paasapi?path=/api/v1/custom/list',
            'delCrowd':'https://databank.tmall.com/api/paasapi',
            'delPath':"/api/v1/crowd/delete",
            'idDetail': 'https://databank.tmall.com/api/paasapi?path=/api/v1/custom',
            'idCnt':'https://databank.tmall.com/api/ecapi?path=/doubleninth/crowd/count' #和策略中心的接口样式差别还挺大的
            }
        }

crowdStatusMap={
    # '全部':'',
    '计算中':'0,3',
    '计算失败':'1,4',
    '计算完成':'2,5'
    }

class WebInteract:
    '''和网页端的request交互'''

    def __init__(self, header,platform):
        '''传入平台名称,绑定相对应的url和api
            '''
        self.header = header
        self.platform = platform
        self.quotaUrl = urlMap[platform]['quota']
        self.crowdListUrl = urlMap[platform]['crowdList']
        self.delCrowdUrl = urlMap[platform]['delCrowd']
        self.delCrowdUrl_2 = urlMap[platform]['delPath']
        self.idDetaiUrl = urlMap[platform]['idDetail']
        self.idCntUrl = urlMap[platform]['idCnt']

    # 检查计算次数信息
    # 拿到header的下一步,直接决定了是否要进行圈包
    # 这是单独的工作
    def checkQuota(self):
        '''无需传参,一次检查应该检查两个内容
            返回计算次数字典'''
        r = requests.get(self.quotaUrl, headers=self.header)
        rJson = json.loads(r.text)
        # exchangeCompute:计算加油包
        exchangeCompute = rJson['data']['quotaPackageVOList']['exchangeCompute']
        # exchangeStoreQuota:存储与用量加油包
        exchangeStoreQuota = rJson['data']['quotaPackageVOList']['exchangeStoreQuota']

        # 每个元素都是字典,一般用name,remainingQuota
        return {_['name']: _['remainingQuota'] for _ in exchangeCompute + exchangeStoreQuota}

    # 同一界面总数查询和二次查询要的东西不太一样
    # page为1太特殊了,传入的1不一定就是默认的,可能是乘除后的结果;不一定就表示获取总数
    def crowdIdQuery(self, keyward, page=1,pageSize=10,crowdStatus='全部'):
        '''按关键词查找ID,返回字典
            单纯查询,输入请求参数,返回响应两种模式,既可以类外看,也能在删除过程中传递信息
            不用可变关键字传参,外部不知道默认值是什么
            crowdStatus:全部(默认),计算中,计算完成,计算失败
            '''

        # 方法和url绑定
        param = {'keyword': keyward, 'page': page, 'pageSize': pageSize}
        if self.platform =='数据银行': #特殊的参数
            param['source']='CUSTOM'
            param['qualityReportOpened']='all'
            param['type']='4'
            param['category2NotEqualList']='scene_crowd'
            
        if crowdStatus !='全部':
            param['crowdStatus']=crowdStatusMap[crowdStatus] #计算完成;计算中
        
        r = requests.get(self.crowdListUrl, params=param, headers=self.header)

        # 响应信息不给人看,json格式
        return json.loads(r.text)

    def singleIdQuery_detail(self,crowd_id):
        '''精准查询单个ID状况,与ui中的详情模板同一
            不保险,平台的问题
            返回字典'''
        param = {'crowdId': crowd_id}
        if self.platform == '数据银行':  # 特殊的参数
            param['copy'] = 'false'
        r = requests.get(self.idDetaiUrl, params=param, headers=self.header)

        # 响应信息不给人看,json格式
        return json.loads(r.text)

    def _persepctiveRefresh_db(self,crowd_id):
        '''
        无使用场景,准备废弃
        刷新最新的画像
        先不用映射,写死成数银的
        内涵两种接口'''
        r = requests.get('https://databank.tmall.com/api/paasapi',
                         params={'crowdId': crowd_id,
                                 'path': '/api/v1/crowd/bloodCheck',
                                 'bloodSource': 'OFFLINE_GGP'
                                 },
                         headers=self.header
                         )
        print(r.text)

        r = requests.get('https://databank.tmall.com/api/paasapi',
                         params={'crowdId':crowd_id,
                                 'path': '/api/v1/crowd/syncToFactory/preCheck'
                                 },
                         headers=self.header
                         )
        print(r.text) #不一定会用到

        sleep(20) #不能立刻请求,20秒不够用?请求规则不完整?
    def singleIdQuery_cnt(self,crowd_id):
        '''查询人数,'''
        param = {'crowdId': crowd_id}
        r = requests.get(self.idCntUrl, params=param, headers=self.header)
        # 响应信息不给人看,json格式
        return json.loads(r.text) #如果传入虚假id,反馈 '你没有权限使用这个资源'
    
    
    def _crowdExtract(self, mode, textJson):
        '''mode:count-计数,detail-明细'''
        # 参数不是人能提供的,方法隐藏
        if mode == 'count':
            # 返回关键字能匹配多少的人群包
            # 使用者看到后其实什么也不做
            return textJson['data']['total']  # int类型,不需要转换
        elif mode == 'detail':
            # 忽略完整的信息,只返回人群包名和id
            return {_['name']: _['id'] for _ in textJson['data']['list']}

    def _crowdDel(self, crowdDict):
        '''传入包含要删除crowdid的字典,方法把id提取出来形成列表'''
        # 删除操作要有输出模块,用来确认
        liTemp=list(crowdDict.values())
        crowdIDliList=[liTemp[i:i+10] for i in range(0,len(liTemp),10)]
        #必须10个10个删
        for _ in crowdIDliList:
            jdata = {"path": self.delCrowdUrl_2,
                     "crowdIds": _
                     }
    
            # 删除操作返回含SUCCESS的内容
            r = requests.post(self.delCrowdUrl, json=jdata, headers=self.header)
    
            print(r.text)

    def crowdPackDel(self, kw, num,crowdStatus='全部'):
        '''即将删除的包的关键字,要删多少个'''
        # 为末次排序提供可能性
        rltForcnt = self.crowdIdQuery(kw,crowdStatus=crowdStatus)
        #取最后一页一定是不满的,所以要给一个中等的num分批删除,涉及删除的一定要小心!
        #+1保证删的是最后一页,不带+1保证删除足够的数量
        #目前先通过关键字的形式删除
        # page = int(self._crowdExtract('count', rltForcnt) / num) + 1
        allCnt=self._crowdExtract('count', rltForcnt)
        page = int(allCnt / num)
        if not page:#会有零的情况
            page = 1
            num = allCnt
        
        # 按照末尾页数获取crowdidList并删除
        rltForcrow = self.crowdIdQuery(kw, page=page, pageSize=num,crowdStatus=crowdStatus)
        crowdDict = self._crowdExtract('detail', rltForcrow)

        # 删除操作要极其谨慎,应该尽可能多地暴漏信息
        crowdNamelist = [_ for _ in crowdDict.keys()]
        input('即将删除以下内容:\n %s \n共计 %s 个\n任意键确认删除' % (str(crowdNamelist),len(crowdNamelist)))

        self._crowdDel(crowdDict)


    def realTimeCalcu_st(self,customModelStr):
        # 先把传来的Json保存到本地
        url = 'https://strategy.tmall.com/api/scapi'
        poyload = {
            'customModelStr': customModelStr,
            'contentType': "application/json",
            'path': "/api/v1/count/crowd/realtime",
            'withConditionGroup': 'true'
        }

        print('向策略中心api发送实时计算请求')
        return requests.post(url, json=poyload, headers=self.header,proxies={'https':None})

    def customDefCrowd_st(self,customModelStr):
        # 先把传来的Json保存到本地
        url = 'https://strategy.tmall.com/api/scapi'
        poyload = {
            'customModelStr': customModelStr,
            'contentType': "application/json",
            'path': "/api/v1/custom/strategy/group"
        }

        print('向策略中心api发送自定义人群请求')
        return requests.post(url, json=poyload, headers=self.header,proxies={'https':None})


    def customDefCrowd_db(self,customModelStr):
        # 先把传来的Json保存到本地
        url = 'https://databank.tmall.com/api/paasapi'
        poyload = {
            'customModelStr': customModelStr,
            'contentType': "application/json",
            'path': "/api/v1/custom/databank"
        }

        print('向数据银行api发送自定义人群请求')
        return requests.post(url, json=poyload, headers=self.header,proxies={'https':None})

    def preferAna(self,poyload):
        '''
        poyload 是字典形式,放在外部观察
        '''
        url = 'https://strategy.tmall.com/api/scapi'
        print('发送偏好分析请求')
        return requests.post(url, data=json.dumps(poyload), headers=self.header,proxies={'https':None})


    def reportDel_st(self,report_id):
        '''先写死成策略中心的
            report_id 要求数字格式'''
        poyload = {
          "path": "/v2/reportcommon/delete",
          "reportId": report_id
        }
        print('发送删除策略中心报告请求')
        #和删人群一个url,只是报文不同
        return requests.post(self.delCrowdUrl, data=json.dumps(poyload), headers=self.header,proxies={'https':None})


    def reportListDel_st(self,report_idList):
        for _ in report_idList:
            self.reportDel_st(_)

    def lv2TagGet_db(self,lv3TagId):
        '''根据二级标签的名字'''
        
        poyload = {
          "path": "/api/dimension/listAllChildDimension",
          "type": 'TAG',
          "id": lv3TagId
        }
        #和删人群一个url,只是报文不同
        r= requests.get(self.delCrowdUrl, params=poyload,headers=self.header,proxies={'https':None})
        return json.loads(r.text)

    def lv2TagNameIdMap_db(self,lv3TagId):
        t=self.lv2TagGet_db(lv3TagId)
        return {_['name']:_['id'] for _ in t['data']['children'][0]['children']}


    #没办法罗列所有的reportid,只能本地记
    # def _reportListQuery_st(self):
    #     para = {
    #         'path': '/v2/reportcommon/listAvailableCrowd',
    #         'reportType': 'CATEGORY_PREFERENCE_ANALYSIS_REPORT',
    #         'reportVersionList': '2'
    #     }
    #     print('发送删除策略中心报告请求')
    #     #和删人群一个url,只是报文不同
    #     r=requests.post(self.delCrowdUrl, data=json.dumps(poyload), headers=self.header,proxies={'https':None})
    #     return  json.dumps(r)
    #
    #
    # def reportQueryWithKw_st(self,kw=''):
    #     '''类外调用,按关键词筛选报告结果'''
    #
    #     reportInfo=self._reportListQuery_st()
    #     for _ in reportInfo['data']:
    #         print(_)
