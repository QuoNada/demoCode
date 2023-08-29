
import json
from .st_paraMap21 import strategyCates,strategyActions,strategyBrandIds,cateDetail


class StategyCard:
    '''目前只有行为类的卡片,不显式设置init方法'''
    
    def actionBuild(self,action,cateName,brand,rangeDate_From,rangeDate_To):
        '''传入人能理解的内容,什么也不返回
            action:浏览人数,购买人数..
            cateName:大家电,冰箱,空调..
            brand:统帅,西门子,小米..
            rangeDate_From,rangeDate_To yyyyDDmm,八位str格式的数字
            '''
        self.action=action
        self.cateName=cateName
        self.brand=brand
        self.rangeDate_From=rangeDate_From
        self.rangeDate_To=rangeDate_To

        self.__formTrans__() #变量较多,没必要增加环节传来传去
        
        return self
    
    
    @staticmethod
    def _brandExtract(brandName):
        '''传入brand全称,返回所有一个或多个平台id组成的list'''
        li=[]
        for _ in strategyBrandIds:
            if _['name'].find(brandName) != -1: #在列表中查找
                li.append(_['id'])
        
        return li

    @staticmethod
    def _idDiv(Li,kw):
        '''根据类型做id分流'''
        
        li=[]
        for _ in Li:
            if _[1]==kw: #根据类型抽取id
                li.append(_[0])
        return li


    @staticmethod
    def _cateExtract(cateName):
        '''是否细分用参数设定
            比如,热水器既可以找cate2的热水器,也可以在热水器里找全部'''
        li=[]
         #返回所有的细分类目列表
        for d in strategyCates[cateName]: #d是细分类目组成的列表
            li.append(cateDetail[d]) #是一个二元数组
        
        clIdLi=StategyCard._idDiv(li,'cate_leaf')
        c2IdLi=StategyCard._idDiv(li,'cate2')
        
        return c2IdLi,clIdLi
    
    @staticmethod
    def _cateCombine(c2Li,clLi):
        '''类内关于品类的三种模板
            对顺序有要求,先是cate2,再是cate_leaf'''
        
        if clLi and not c2Li:
            return [
                {
                    "cateName": "cate_leaf",
                    "cateIds": clLi
                }
                ]
        elif not clLi and c2Li:
            return [
                {
                    "cateName": "cate2",
                    "cateIds": c2Li
                }
                ]
        elif clLi and c2Li:
            return [
                {
                    "cateName": "cate2",
                    "cateIds": c2Li
                },
                {
                    "cateName": "cate_leaf",
                    "cateIds": clLi
                }
            ]
        
    def __formTrans__(self):
        '''需要总结出cate2和cate_leaf的关系'''
        
        
        self.actionType=strategyActions[self.action]
        
        self.cates=self._cateCombine(*self._cateExtract(self.cateName)) #列表格式
        self.brandIds=self._brandExtract(self.brand) #列表格式
    


class StategyTemple:
    '''行为模板读取+组装,暂时只有行为类卡片'''
    
    def __init__(self,templePath,crowdName=None):
        '''传入人群包名和本地模板路径
            实时计算就不需要包名'''
        
        self.crowdName=crowdName #包名需要保留,供外部查看
        self.templePath=templePath
    
    
    def __templeRead__(self):
        with open(self.templePath,'r',encoding='utf-8') as f:
            return json.load(f)
            
    def __fillCerternCard__(self,temple,ActionCard,ActionCardIndex,relation=''):
        '''没有用到成员变量,仅仅是内部调用
            拼模板就是 a=xxx,处理的功能放在卡片构建的类中'''
        
        if relation: #不是所有模板都有交并差
            temple['groupCards'][0]['children'][ActionCardIndex]['op']=relation
        
        temple['groupCards'][0]['children'][ActionCardIndex]['data']['actionType']=ActionCard.actionType
        #使用了浅拷贝特性,修改action 就等于 修改temple
        actionCard=temple['groupCards'][0]['children'][ActionCardIndex]['data']['actionData']
        actionCard['cates']=ActionCard.cates
        actionCard['brandIds']=ActionCard.brandIds
        actionCard['rangeDate']['from']=ActionCard.rangeDate_From
        actionCard['rangeDate']['to']=ActionCard.rangeDate_To
        
        return temple
    
    def singleAction(self,ActionCard,perspective):
        '''模板相对静态,对比京东简单很多,默认有包名
            要选择是否开启透视'''
        #其他的方法先不管透视问题
        
        temple=self.__templeRead__()
        if self.crowdName:
            temple['crowdName']=self.crowdName
        if perspective:
            temple['startPerspective']=1
        #唯一能体现该方法独特性的标识,列表中第0个元素
        return self.__fillCerternCard__(temple,ActionCard, 0) #返回组装好的模板
    
    
    
    def twoAction(self,relation,ActionCard1,ActionCard2):
        '''先暂时不设置人群名,先在实时计算中使用'''
        temple=self.__templeRead__()
        if self.crowdName:
            temple['crowdName']=self.crowdName
            
        temple=self.__fillCerternCard__(temple,ActionCard1, 0)
        return self.__fillCerternCard__(temple,ActionCard2, 1,relation=relation)
        

    def threeAction(self,relation1,ActionCard1,ActionCard2,relation2,ActionCard3):
        '''先暂时不设定是浏览还是购买,统称为卡片'''
        
        temple=self.__templeRead__()
        if self.crowdName:
            temple['crowdName']=self.crowdName

        temple=self.__fillCerternCard__(temple,ActionCard1, 0)
        temple=self.__fillCerternCard__(temple,ActionCard2, 1,relation=relation1)
        return self.__fillCerternCard__(temple,ActionCard3, 2,relation=relation2)

