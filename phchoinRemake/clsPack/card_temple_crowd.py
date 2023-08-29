# -*- coding: utf-8 -*-
"""
Created on Mon May 22 14:42:44 2023

@author: chenyue
这次不再引入那么多的映射关系,因为映射关系既可以从本地拿,可以从接口读
需要在模块级解耦
相应的,主流程调用方法时就需要引入各种映射,并传参
"""
import json
import os
from os import path

#先准备1级标签,基本是死的,mapTagBuild会使用
lv1Map={'BasicTag':'基础标签',
        'IndusTag':'行业标签',
        'LifeTag':'生活方式',
        'FunPerferTag':'娱乐偏好',
        'ExclusiveTag':'专属标签'
        }

class CardDB:
    '''
    没有实例化方法    
    从setCritetia方法 或 定义criteriaFile/attributeFile 开始
    主要关注lv3内容的定义和处理
    准备模板就是准备最大重合度的可复用壳
    '''
    
    #卡片的变形不太好定义,从响应里只知道是children
    def setCriteria(self,criteriaFile,criteria1,criteria2):
        '''criteria 是条件列表内容
            无论不同的卡片内参数的键值要求多么不一样,但都在同一个响应中罗列
            但有些方法放开了就不强制实例化参数了'''
        self.criteriaFile=criteriaFile
        self.criteria1=criteria1
        self.criteria2=criteria2
    
        return self
    
    def _getParaValue_db(self):
        '''
        构建本地保存的卡片描述全映射筛选需要的值
        不依赖本地人定义零散的映射关系
        '''
        
        #虽然也是从json读映射关系,但是输出的内容是特征化的,不能单独成为方法
        #还需要抽取更多有用的信息
        with open(self.criteriaFile,'r',encoding='utf-8') as f:
            jsonf=json.load(f)#仅仅是数银的映射文件有效
        
        for d1 in jsonf['data']['children']: #_是类型
            '''循环中拿到目标值就返回'''
            #还需要继续循环
            if d1['name'] == self.criteria1:
                for d2 in d1['children']:
                    if d2['name']==self.criteria2:
                        #不关心里面的内容是不是和画像的标签有关系
                        return {'criteria1Name':d1['name'],
                                'criteria1Id':d1['id'], #要用两次
                                'criteria1Prop':d1['extraProp']['value'], 
                                'criteria2Name':d2['name'],
                                'criteria2Id':d2['id'],
                                'criteria2Aid':d2['aid'],
                                'criteria2Prop':d2['extraProp']['value'], 
                            }
    
    def _lv1Init(self,templeFile=''):
        '''
        可以不传模板文件
        模板文件也可不留editUsefulData位置
        '''
        
        m1=self._getParaValue_db() #对输出引用需要知道都有那些键
        
        if templeFile:
            with open(templeFile,'r') as f:
                Card=json.load(f)
        else:
            Card={"selectionLv1":[],"selectionLv3":{}}
        
        #不论模板有没有editUsefulData键都行,增加灵活性
        if Card.get('editUsefulData'):
            Card['editUsefulData']['aliId']=[m1['criteria1Id'],m1['criteria2Aid']]
            Card['editUsefulData']['uniqueId']=[m1['criteria1Id'],m1['criteria2Id']]
            Card['editUsefulData']['conditionName']=' > '.join([self.criteria1,self.criteria2])
            Card['editUsefulData']['getDimensionId']=m1['criteria2Aid']
            
        Card['selectionLv1']=[m1['criteria1Prop'],m1['criteria2Prop']] #主要拿lv1的内容
    
        return Card
    
    
    
    
    def attributeCard_fill(self,attributeFile,keyName,tagDetailDict,selectValues,selectValuesDict):
        '''
        attributeFile 属性圈人卡片空模板
        keyName 标签名,str
        tagDetailDict 标签名映射,可以是mapTagBuild返回的某个值
        attriValue 属性值,list
        selectValuesDict 属性值映射
        主流程调用,只有主流程才知道要传什么值进来,但是要把映射也传进来
        需要提前定义selectValuesDict变量
        后续的依赖映射会新开其他类
        '''
        aCard=self._lv1Init(attributeFile)
        
        #依赖外部很细的映射
        aCard['selectionLv3']['attributes'][0]['key']='{v}#|#{v}'.format(
            v=tagDetailDict[keyName])
        
        aCard['selectionLv3']['attributes'][0]['selectValues']= ['{v}#|#{v}'.format(
            v=selectValuesDict[_]) for _ in selectValues]

        return aCard
    
    def fullLinkCard_fill(self,fullLinkFile,cateName,cateDict,types,typeDict,dateValue,**kwargs):
        '''
        cateName str
        types AIPL需要大写,list
        dateValue 字串'yyyyMMdd'或者字典{from:,to:}
            全链路状态 字典
            全链路历史 字串
        kwargs 
            dayCounts,需要结果列表以及dayCountDict映射
        无论是链路状态还是链路历史,都默认模板是绝对时间
        '''
        
        fCard=self._lv1Init(fullLinkFile)
        
        if cateName=='全部':
            fCard['selectionLv3']['cate']=cateDict[cateName]
        else:
            fCard['selectionLv3']['cate']='{v}#|#{v}'.format(v=cateDict[cateName])
        
        fCard['selectionLv3']['types']= [typeDict[_] for _ in types]
        fCard['selectionLv3']['dateValue']=dateValue
        
        if kwargs.get('dayCounts'): #不一定会用得到,先准备着
            fCard['selectionLv3']['dayCounts']=[kwargs['dayCountDict'][_] for _ in kwargs['dayCounts']]
        
        return fCard
    
    def prodActionCard_fill(self,channel='',channeltMap={},
                            shop='',shopIds={},
                            bhv=[],actions={},
                            cate='',cateIds={},
                            types=[],itemFullLinkStage={},
                            selectedGoodsType='',selectedGoodsTypeMap={},items=[],
                            dateType='ABSOLUTE_DATE_RANGE',dateValue={},
                            tmall=True,
                            **kwargs):
        '''
        不准备本地模板,lv2也要求主流程传
        名称尽量简单
        已有kwargs
            channel 渠道,天猫...
                需要channeltMap做映射
                不同的卡片要准备不同映射,比如都是天猫,商品订单是14266,商品行为是63
            shop,店铺名
                引用店铺id,和重代码的shop_id对应
                需要shopIds做映射
            bhv,行为,list
                浏览行为,购买行为
                需要actions做映射,不同的卡片要准备不同映射,不一定能混用
            cate str
                None,全部,品类码
                需要cateIds做映射,全链路卡片也有此参数
            types,状态,list
                A I P L
                需要itemFullLinkStage做映射,和全链路的映射不一样
            selectedGoodsType 商品挑选模式
                1 品牌任意商品
                2 指定商品ID,多一个必传的 items参数,list
                    映射以id做键,在使用侧声明,构建侧不需要单品昵称
                    业务能提供ID,毕竟是卡片要求的
                3 指定商品
                需要selectedGoodsTypeMap做映射
            dateType 默认ABSOLUTE_DATE_RANGE
            dateValue {from: ,to:}
        待扩展kwargs
            keywords
            frequency
            money
            status
            payDateValue,orderDateValue
            
        以货圈人四种卡片相差太大了,要求调用者传入相关的可变参数要符合格式
        '''
        
        fCard=self._lv1Init() #本地不保存模板
        if channel:
            fCard['selectionLv2']=[channeltMap[channel]] #要求列表
            fCard['selectionLv2Name']=channel
        
        #键值内容一律用字典的增加形式
        t=fCard['selectionLv3'] #t为空字典
        if shop:
            t['shop']=shopIds[shop] if shop=='全部' else '{v}#|#{v}'.format(v=shopIds[shop])
            
        if bhv:
            t['bhv']=[actions[_] for _ in bhv]

        if selectedGoodsType:
            t['selectedGoodsType']=selectedGoodsTypeMap[selectedGoodsType]
            if selectedGoodsTypeMap[selectedGoodsType]==2:
                t['item']=items
        
        if dateType:#默认会进入
            t['dateType']=dateType
            t['dateValue']=dateValue
        
        
        return fCard
    
    
    @staticmethod
    def mapTagBuild(tagDir):
        '''
        返回字典
            tagMap_enk,tagMap_zhk
            tagLv2_idk,tagLv2_namek
        构建英文_中文的3级映射,以及id内容
        对类外暴露,定义好tagDir 就能用
        有个问题,没有对修改关闭,等需要更多内容的时候还需要调
        '''
        #再准备2级标签
        tagMap_enk={}
        tagLv2_idk={}
        for _ in os.listdir(tagDir):
            lv1TagName=lv1Map[_.split('.')[0]]
            with open(path.join(tagDir, _),'r',encoding='utf-8') as f:
                jsonf=json.load(f)
                for li1 in jsonf['data']: #li1是字典
                    tagLv2_idk[li1['tagCateId']]=li1['tagCateName']
                    #都有data键,lv1可遍历内容很少
                    for li2 in li1['tagPropList']: #只要li2的两个键
                        tagMap_enk[li2['tagId']]='_'.join((lv1TagName,li1['tagCateName'],li2['tagTitle']))
        
        #返回所有的遍历内容,下游根据键来调用
        #两个字典反转
        return {
                'tagMap_enk':tagMap_enk,
                'tagMap_zhk':{v:k for k,v in tagMap_enk.items()},
                'tagLv2_idk':tagLv2_idk,
                'tagLv2_namek':{v:k for k,v in tagLv2_idk.items()}
                }
    
    @staticmethod
    def value4Query(lv2WholeDict,kw,reverse=False):
        '''
        lv2wholeDict 是请求lv2接口的能囊括3级,4级信息的整全信息
        kw是自然语言 比如预测年龄
        靠近主流程,内容上跟本类关系不大
        可能需要反转的,因为值更容易理解
        映射准备阶段比较方便,不用一个个点拿平台id
        '''
        info4={}
        for li1 in lv2WholeDict['data']['children']:
            if li1['name']==kw:
                for li2 in  li1['children']:
                    info4[li2['id']]=li2['name']
        if reverse:
            return {v:k for k,v in info4.items()}
        
        return info4 #不反转就用平台id做标识

class TempleDB:
    
    def __init__(self,templePath,crowdName=None):
        '''传入人群包名和本地模板路径
            实时计算就不需要包名'''
        
        self.crowdName=crowdName #包名需要保留,供外部查看
        self.templePath=templePath #就两个键,crowdName和list
    
    def _templeRead(self):
        '''读取'''
        with open(self.templePath,'r',encoding='utf-8') as f:
            return json.load(f)
    
    
    def _opAttach(self,DataBankCard,op=None):
        
        if op:#如果是第一个卡片就不需要op
            DataBankCard['op']=op
            
        return DataBankCard
    
    #用到模板才有关系的出现
    def fillTemple(self,DataBankCard0,**kwargs):
        '''显式传入直接的opINTERSECT,UNION,DIFF
            关键词传入op#,DataBankCard#
                op是必须的,用来做判断
            简单的append
            '''
        temple=self._templeRead()
        temple['crowdName']=self.crowdName
        
        temple['list'].append(self._opAttach(DataBankCard0))
        if kwargs.get('op1',None):
            temple['list'].append(self._opAttach(kwargs['DataBankCard1'],kwargs['op1']))
            
        if kwargs.get('op2',None):
            temple['list'].append(self._opAttach(kwargs['DataBankCard2'],kwargs['op2']))
            
        if kwargs.get('op3',None):
            temple['list'].append(self._opAttach(kwargs['DataBankCard3'],kwargs['op3']))
            
        if kwargs.get('op4',None):
            temple['list'].append(self._opAttach(kwargs['DataBankCard4'],kwargs['op4']))
            
        return temple
    

    def fillTemple_even(self,DataBankCard0,**kwargs):
        '''
        如果卡片太多会产生很多冗余
        要求op#,DataBankCard#的形式
        '''
        temple=self._templeRead()
        temple['crowdName']=self.crowdName
        
        temple['list'].append(self._opAttach(DataBankCard0))
        for i in range(1,int(len(list(kwargs.keys())) / 2) + 1):
            #知道kwargs的长度就能确定要循环多少次
            temple['list'].append(self._opAttach(kwargs['DataBankCard%s' % i],kwargs['op%s' % i]))
            
        return temple
        
            
            