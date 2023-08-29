# -*- coding: utf-8 -*-
"""
Created on Mon Apr 10 16:03:23 2023

@author: chenyue
"""

import json
from db_paraMap22 import cateIds,databanActions,databankShopIds,selectedGoodsTypeMap \
    ,itemFullLinkStage,fullLinkStage,cateIds

#相当于是3中类型分别对应业务的3种需要卡片
#要拆开做
class DataBankCard:
    '''cardType
            商品行为,商品互动人群全链路状态,全链路状态
        品类,起止日期都是3种卡片共有的一次性传入所有参数也行
        可选项:
            shop,店铺名
                引用店铺id,和重代码的shop_id对应
            bhv,行为,列表
                浏览行为,购买行为
            cate 
                None,全部,品类码
            types,状态,列表
                A I P L
            selectedGoodsType 商品挑选模式
                1 品牌任意商品
                2 指定商品ID,多一个必传的 item参数,列表形式
                    映射以id做键,在使用侧声明,构建侧不需要单品昵称
                    业务能提供ID,毕竟是卡片要求的
                3 指定商品
    '''
    
    
    #这些卡片揉到了一块
    def __init__(self,cardType,cate,rangeDate_From,rangeDate_To,**kwargs):
        self.cardType=cardType
        self.rangeDate_From=rangeDate_From
        self.rangeDate_To=rangeDate_To
        #品类不能直接用
        if cate != '全部': #比较特殊的一种
            self.cate='%s#|#%s' % (cateIds[cate],cateIds[cate])
        else:
            self.cate=cateIds[cate]

        #传入非共有参数
        self.fillPara(**kwargs)
    
    def fillPara(self,**kwargs):
        '''调用映射关系,返回可用于拼接的形式化参数
            也是传人能理解的东西,传多了没事,传少了影响模板拼接
            也可类外调用
        '''
        #初始化一些变量,不至于拼接的时候报错
        self.setSomeAttr(['shop','bhv','selectedGoodsType','types'])
        
        if kwargs.get('shop',''):#字串
            shopId=databankShopIds[kwargs['shop']]
            if shopId=='ALL':
                self.shop=shopId
            else:
                self.shop='%s#|#%s' % (shopId,shopId)
        
        if kwargs.get('bhv',[]):#行为可以多选,所以入参也要选列表
            self.bhv=[databanActions[_] for _ in kwargs['bhv']]
        
        if kwargs.get('selectedGoodsType',''):
            self.selectedGoodsType=selectedGoodsTypeMap[kwargs['selectedGoodsType']] #字串
            if self.selectedGoodsType =='2':
                self.item=kwargs['item']
        
        if kwargs.get('types',[]) and self.cardType=='商品互动人群全链路状态':
            self.types=[itemFullLinkStage[_] for _ in kwargs['types']]
        
        if kwargs.get('types',[]) and self.cardType=='全链路状态':
            self.types=[fullLinkStage[_] for _ in kwargs['types']]
            
    
    def setSomeAttr(self,attrList):
        for _ in attrList:
            setattr(self,_,None)
        
        

class DataBankTemple:
    
    
    def __init__(self,templePath,crowdName=None):
        '''传入人群包名和本地模板路径
            实时计算就不需要包名'''
        
        self.crowdName=crowdName #包名需要保留,供外部查看
        self.templePath=templePath
    
    
    def _templeRead(self):
        '''读取'''
        
        with open(self.templePath,'r',encoding='utf-8') as f:
            return json.load(f)

    
    def _fillUnitCard(self,temple,Card,CardIndex,op=''):
        '''没有用到成员变量,仅仅是内部调用
            拼模板就是 a=xxx,处理的功能放在卡片构建的类中
            和卡片类耦合很深'''
        
        if op: #不是所有模板都有交并差
            temple['list'][CardIndex]['op']=op
        
        #默认浅拷贝
        sl3=temple['list'][CardIndex]['selectionLv3']
        
        if Card.bhv:
            sl3['bhv']=Card.bhv #列表
            
        if Card.shop:
            sl3['shop']=Card.shop #店铺码,字串
            
        if Card.selectedGoodsType:
            sl3['selectedGoodsType']=Card.selectedGoodsType
            if Card.selectedGoodsType == '2': #多一个参数
                sl3['item']=Card.item
        
        if Card.types:#不关心是哪种aipl映射
            sl3['types']=Card.types
        
        sl3['cate']=Card.cate #字串
        sl3['dateValue']['from']=Card.rangeDate_From
        sl3['dateValue']['to']=Card.rangeDate_To
        
        return temple    



    def fillTemple(self,DataBankCard0,**kwargs):
        '''目前只有两种可能,但也要把更多卡片的组合形式开出来,因为其他卡片有3种的情况
            如果有两个卡片要显式传入直接的opINTERSECT,UNION,DIFF
            这次把行为的全部集中起来,在策略中心的基础上迭代
            关键词传入op#,DataBankCard#
                op是必须的,用来做判断'''
        temple=self._templeRead()
        temple['crowdName']=self.crowdName
        temple=self._fillUnitCard(temple, DataBankCard0, 0)
        if kwargs.get('op1',None):
            temple=self._fillUnitCard(temple, kwargs['DataBankCard1'], 1,kwargs['op1'])
        
        if kwargs.get('op2',None):
            temple=self._fillUnitCard(temple, kwargs['DataBankCard2'], 2,kwargs['op2'])
        
        if kwargs.get('op3',None):
            temple=self._fillUnitCard(temple, kwargs['DataBankCard3'], 3,kwargs['op3'])
        
        return temple
    
    
    
    
    