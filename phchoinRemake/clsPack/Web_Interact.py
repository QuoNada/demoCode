# -*- coding: utf-8 -*-
"""
Created on Tue Feb 14 15:03:29 2023

@author: chenyue

"""
import json, requests
from time import sleep
import warnings

def deprecate(func):
    def wrapper(*args, **kwargs):
        warnings.warn(f"{func.__name__} is deprecated.", DeprecationWarning, stacklevel=2)
        return func(*args, **kwargs)
    return wrapper

#策略中心的quota接口是个特殊的paasapi
#有些接口可以精简,
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

class WebBase:
    '''和网页端的request交互'''

    def __init__(self, header,platform):
        '''
        传入平台名称,绑定相对应的url和api
        变量太多,也不会类外调用,就隐藏起来
        '''
        self.header = header
        self.platform = platform
        self._quotaUrl = urlMap[platform]['quota']
        self._crowdListUrl = urlMap[platform]['crowdList']
        self._delCrowdUrl = urlMap[platform]['delCrowd']
        self._delCrowdUrl_2 = urlMap[platform]['delPath']
        self._idDetaiUrl = urlMap[platform]['idDetail']
        self._idCntUrl = urlMap[platform]['idCnt']


    @deprecate
    def _persepctiveRefresh_db(self,crowd_id):
        '''
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


class WebQuery(WebBase):
    '''
    查询 计算次数/模糊人群列表/单人群详情/单人群人数
    '''
    
    def checkQuota(self):
        '''
        检查计算次数信息
        无需传参,一次检查应该检查两个内容
        返回计算次数字典
        '''
        r = requests.get(self._quotaUrl, headers=self.header,proxies={'https':None})
        rJson = json.loads(r.text)
        exchangeCompute = rJson['data']['quotaPackageVOList']['exchangeCompute'] #计算加油包
        exchangeStoreQuota = rJson['data']['quotaPackageVOList']['exchangeStoreQuota'] #存储与用量加油包

        # 每个元素都是字典,一般用name,remainingQuota
        return {_['name']: _['remainingQuota'] for _ in exchangeCompute + exchangeStoreQuota}

    # 同一界面总数查询和二次查询要的东西不太一样
    # page为1太特殊了,传入的1不一定就是默认的,可能是乘除后的结果;不一定就表示获取总数
    def crowdIdQuery(self, keyward, page=1,pageSize=10,crowdStatus='全部'):
        '''
        按关键词查找ID,返回字典
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
        
        r = requests.get(self._crowdListUrl, params=param, headers=self.header)

        # 响应信息不给人看,json格式
        return json.loads(r.text)

    def singleIdQuery_detail(self,crowd_id):
        '''
        精准查询单个ID状况,与ui中的详情模板同一
        返回字典
        '''
        param = {'crowdId': crowd_id}
        if self.platform == '数据银行':  # 特殊的参数
            param['copy'] = 'false'
        r = requests.get(self._idDetaiUrl, params=param, headers=self.header)

        # 响应信息不给人看,json格式
        return json.loads(r.text)
    
    def singleIdQuery_cnt(self,crowd_id):
        '''查询人数,'''
        param = {'crowdId': crowd_id}
        r = requests.get(self._idCntUrl, params=param, headers=self.header)
        # 响应信息不给人看,json格式
        return json.loads(r.text) #如果传入虚假id,反馈 '你没有权限使用这个资源'
    
    
    #可以减少本地映射关系的保留
    #但是需要准备的东西也不少,比如一个lv3下有多个lv4维度
    #同时接口涉及到有效信息密度的问题
    #标签是个大工程,等需求复杂度更高了会变得必要,比如属性圈人的卡片超过半数
    #如果是其他的卡片可能性比较少,使用本地罗列的方式做,也容易维护
    def _lv4TagGet_db(self,lv3TagId):
        '''
        传入二级标签的id
            比如基础标签-基础属性,1,快消行业40,美妆行业6
            这样的信息需要从2/3级的映射中寻找
            比如brand1有5类一级标签,本地准备了5个json
            不同品牌的lv3内容范畴不一样,跟账号拥有的标签授权有关,所以不能和这个类耦合
            需要在靠近主流程的类里找拿lv2_id映射的方法
        返回包含三级和四级元素的id映射的大全内容
            比如预测年龄:daas_tag_pred_age_level_20200415093010
            比如都市蓝领:1,100~200:601044725
        暂时先不用在生产的主流程中,获取网页信息的时候做辅助用
        '''
        poyload = {
          "path": "/api/dimension/listAllChildDimension",
          "type": 'TAG',
          "id": lv3TagId
        }
        #和删人群一个url,只是报文不同
        r= requests.get(self._delCrowdUrl, 
                        params=poyload,
                        headers=self.header,
                        proxies={'https':None})
        
        return json.loads(r.text) 
        #到此是接口的动作,如何按标签抽取内容是数据处理的任务
        #之前写的有问题,直接默认第0个元素就是目标集合,其实应该按照关键字
    

    def cate2Get_st(self):
        '''
        获取策略中心一个品牌下的所有cate2和cateleaf
        '''
        poyload = {
            "path":"/api/v1/category/strategy/listRelation",
            "cate1Flag": 'false',
        }

        # 和删人群一个url,只是报文不同
        r = requests.get(self._delCrowdUrl,
                         params=poyload,
                         headers=self.header,
                         proxies={'https': None})

        #响应解析放在其他地方做
        return json.loads(r.text)


    def reportListQuery_st(self,reportTypeName):
        '''
        :param reportTypeName: 相关性分析/品类偏好分析
        :return:
        '''
        if reportTypeName=='品类偏好分析':
            para = {
                'path': '/v2/reportcommon/listAvailableCrowd',
                'reportType': 'CATEGORY_PREFERENCE_ANALYSIS_REPORT',
                'reportVersionList': '2'
            }
        elif reportTypeName=='相关性分析':
            para = {
                'path': '/v2/reportcommon/listAvailableCrowd',
                'reportType': 'CORRELATION_ANALYSIS_REPORT',
                'isTrendMode': 'undefined'
            }

        #和删人群一个url,只是报文不同
        r=requests.get(self._delCrowdUrl, params=para, headers=self.header,proxies={'https':None})

        return json.loads(r.text)



class WebCalcu(WebBase):
    '''
    人群圈选/实时计算/品类偏好分析
    '''
    
    
    def realTimeCalcu_st(self,customModelStr):
        '''
        实时计算
        '''
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
        '''
        策略中心自定义人群
        '''
        url = 'https://strategy.tmall.com/api/scapi'
        poyload = {
            'customModelStr': customModelStr,
            'contentType': "application/json",
            'path': "/api/v1/custom/strategy/group"
        }

        print('向策略中心api发送自定义人群请求')
        return requests.post(url, json=poyload, headers=self.header,proxies={'https':None})


    def customDefCrowd_db(self,customModelStr):
        '''
        数据银行自定义人群
        '''
        url = 'https://databank.tmall.com/api/paasapi'
        poyload = {
            'customModelStr': customModelStr,
            'contentType': "application/json",
            'path': "/api/v1/custom/databank"
        }

        print('向数据银行api发送自定义人群请求')
        return requests.post(self._delCrowdUrl, json=poyload, headers=self.header,proxies={'https':None})


    def preferAna(self,crowdId,startDate,endDate,targetCateIdList):
        '''
        策略中心品类偏好分析
        targetCateIdList 品类id的列表
        默认是天猫渠道
        '''
        payload = {  # 拼接报告模板
            'contentType': 'application/json',
            'crowdId': crowdId,
            'channelCodes': ["4"],
            'startDate': startDate,
            'endDate': endDate,  # 最多30天
            'name': '品类偏好分析',  # 也可以自定义,也可以默认
            'paramReportType': 'CATEGORY_PREFERENCE_ANALYSIS_REPORT',
            'path': '/v2/reportcommon/create',
            'targetCateIdList': targetCateIdList,
            'timePeriod': 'D'
        }

        print('发送偏好分析请求')
        return requests.post(self._delCrowdUrl, data=json.dumps(payload), headers=self.header,proxies={'https':None})


    def corrAna(self,crowdId,endDate,dateType):
        '''
        策略中心相关性分析
        crowdId int
        endDate int,8位,最多是昨天
        dateType 倒推天数,int
        默认天猫渠道
        '''
        payload={
            "paramReportType": "CORRELATION_ANALYSIS_REPORT",
            "path": "/v2/reportcommon/create",
            "contentType": "application/json",
            "crowdId": crowdId,
            "name": "相关性分析",
            "endDate": endDate,
            "dateType": dateType,
            "tgiCompareRangeType": "All",
            "tgiCompareRangeCrowdId": None,
            "channelCodes": [
                "4"
            ]
        }
        print('发送相关性分析请求')
        return requests.post(self._delCrowdUrl, data=json.dumps(payload), headers=self.header,proxies={'https':None})

class WebDel(WebQuery):
    '''
    删人群/删报告
    不需要从Base类继承
    '''
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
            jdata = {"path": self._delCrowdUrl_2,
                     "crowdIds": _
                     }
    
            # 删除操作返回含SUCCESS的内容
            r = requests.post(self._delCrowdUrl, json=jdata, headers=self.header)
    
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

    def reportDel_st(self,report_id):
        '''先写死成策略中心的
            report_id 要求数字格式'''
        poyload = {
          "path": "/v2/reportcommon/delete",
          "reportId": report_id
        }
        print('发送删除策略中心报告请求')
        #和删人群一个url,只是报文不同
        return requests.post(self._delCrowdUrl, data=json.dumps(poyload), headers=self.header,proxies={'https':None})


    def reportListDel_st(self,report_idList):
        for _ in report_idList:
            self.reportDel_st(_)

    
