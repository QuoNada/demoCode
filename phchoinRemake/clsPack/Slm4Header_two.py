# -*- coding: utf-8 -*-
"""
Created on Wed Apr 26 15:31:21 2023

@author: chenyue
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException,TimeoutException,WebDriverException
from selenium.webdriver import ActionChains 

import os
os.chdir(os.path.dirname(__file__)) #可识别相对路径
import json
import requests
import time

#全局映射
authMap={
    '策略中心':'https://strategy.tmall.com/api/checkDataBankAuth?',
    '数据银行':'https://databank.tmall.com/api/smartapi?path=/api/v1/user/listBrandProperties',
    }

class SLMlogin:
    '''selenium操作'''

    #有个问题,不一定都要登录
    def __init__(self,account='', password=''):
        '''实例化对象可以调用类属性,driver
            newBroswer 由另一个类传入'''
        self.account=account
        self.password=password
        
    def driverSet(self):
        '''主要以登录流程为主,线性内容'''
        
        options = webdriver.ChromeOptions()
        options.add_experimental_option('detach', True) #不自动关闭浏览器
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("useAutomationExtension", False)
        service = ChromeService(executable_path='D:/TestProject/chromedriver.exe')
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
          "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
        })
        driver.maximize_window()
        self.driver=driver
    
    def dragSlideBlock(self):
        '''拖动滑块,基本都能成功,验证不算复杂
            不一定要怎么使用,先封成方法'''
        driver=self.driver
        try:
            iframe=driver.find_element(by=By.ID,value='baxia-dialog-content')
            driver.switch_to.frame(iframe) #滑块iframe
        
            # 确定滑块宽度，高度
            block=driver.find_element(by=By.ID,value='nc_1_n1z')
            # 确定滑道宽度，高度
            slide=driver.find_element(by=By.CLASS_NAME,value='nc-lang-cnt')
        
            ActionChains(driver).drag_and_drop_by_offset(block,slide.size["width"],block.size['height']).perform()
        except:
            driver.refresh()
            return False
    
    def queryTokenCookie(self):
        '''加载主页后获取header信息
            aliLoginWithSb两个地方return,额外分出方法
            一处构建,两处使用'''
        #拿到cookie和token,在另一个类里组装到头里
        driver=self.driver
        token=driver.find_element(by=By.XPATH,value=
            '/html/head/meta[@name="_csrf"]').get_attribute('token')
        
        cookie=driver.get_cookies()
        return {'token':token,'cookie':cookie}


    def aliLoginWithSb(self,platfrom):
        '''运行selenium,调用此方法才新开浏览器
            返回cookie+token
            包含对滑块的处理,需要人值守
            platfrom 策略中心/数据银行
            '''
        self.driverSet()
        driver=self.driver
        
        #新增加的内容
        if platfrom=='数据银行':
            driver.get('https://databank.tmall.com/')
            iframe=driver.find_element(by=By.CLASS_NAME,value='login-iframe')
        elif platfrom=='策略中心':
            driver.get('https://strategy.tmall.com/')
            iframe=driver.find_element(by=By.ID,value='tbLoginFrame')
    
        driver.switch_to.frame(iframe) #内嵌iframe
        
        try:#传递账密
            driver.find_element(by=By.ID,value='fm-login-id').send_keys(self.account)
            driver.find_element(by=By.ID,value='fm-login-password').send_keys(self.password)
            driver.find_element(by=By.CLASS_NAME,value='fm-btn').click() #登录
        except NoSuchElementException:
            driver.refresh()
            input('请手动输入账密,进入主页后回车')
            #已经介入人工了,没必要再往下走了,提早返回,拿header只是第一步
            return self.queryTokenCookie()
        
        #不稳定,对使用者要求太高
        wait=WebDriverWait(driver,10) #设置等待机制,限时10s操作
        try:
            #如果wait报错,就不会findelement报错
            element=wait.until(EC.visibility_of_all_elements_located(
                    (By.CSS_SELECTOR,'.fm-button.fm-submit.password-login.fm-button-disabled'))) #进入策略中心
            
            #如果登录不能点,就要拖动滑块
            if not driver.find_element(by=By.CSS_SELECTOR,value='.fm-button.fm-submit.password-login.fm-button-disabled').is_selected():
                self.dragSlideBlock() #也可能会失败
            else:
                element.cilck()
            
            #策略中心和数据银行要做开分支,以后需要加上
            if platfrom=='数据银行':
                element=wait.until(EC.element_to_be_clickable(
                        (By.CLASS_NAME,'enter-databank-button'))) 
            elif platfrom=='策略中心':
                element=wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR,'.primary-button.turn-databank-btn'))) 
            
            element.click()
        
        #看到主页内容之前可能要好一会,但只要有加载行为就足够了,不需要真的看到内容
        except (TimeoutError,TimeoutException,WebDriverException):
            input('登录主页后回车')
        
        return self.queryTokenCookie()


    def aliLoginWithDriver(self,platfrom):
        '''已经有了driver的情况下
            '''
        driver=self.driver
        #新增加的内容
        #只能第一次这么做,
        if platfrom=='数据银行':
            driver.get('https://databank.tmall.com/')
        elif platfrom=='策略中心':
            driver.get('https://strategy.tmall.com/')
    
        wait=WebDriverWait(driver,10) #设置等待机制,限时10s操作
        try:
            #策略中心和数据银行要做开分支,以后需要加上
            if platfrom=='数据银行':
                element=wait.until(EC.element_to_be_clickable(
                        (By.CLASS_NAME,'enter-databank-button'))) 
            elif platfrom=='策略中心':
                element=wait.until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR,'.primary-button.turn-databank-btn'))) 
            
            element.click()
        #看到主页内容之前可能要好一会,但只要有加载行为就足够了,不需要真的看到内容
        except (TimeoutError,TimeoutException,WebDriverException):
            input('登录主页后回车')
        
        return self.queryTokenCookie()


class HeaderResolve:
    '''头文件的本地读写+验证
        不关心外部的服务平台'''
    
    headerTemple={
            "user_agent":
                "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
            'content-type': 'application/json'
            }
    
    
        
    def __init__(self,platform,localPath):
        '''和本地的json文件对应,如果没有就创建'''
        self.platform=platform    
        self.localPath=localPath    
    
    def localFileHandle(self,mode,loginInfo=''):
        '''如果本地不存在什么也不做
            token+cookie组合,cookie是get方法直接获得的
            loginInfo 是queryTokenCookie方法的返回结果'''
        if mode=='read':
            if os.path.exists(self.localPath):
                with open(self.localPath,'r',encoding='utf-8') as f:
                    content=json.load(f)
                return content
            #文件不存在返回空,直接进入selenium过程
            return
        elif mode == 'write' and loginInfo:
            with open(self.localPath,'w') as f:
                json.dump(loginInfo,f)
            
            print('新的token+cookie已写入本地文件')

    @classmethod
    def headerOfBroswer(cls,Infojson):
        '''维持原生格式,cookie存在列表中,token存在字串中
            不应该分开,全部来源都是json
            可能来自selenium,可能来自本地'''
        headerTemple=cls.headerTemple.copy() #深拷贝!!!
        #列表中的字典提取name,value并转字串
        
        if Infojson.get('token',False):#数坊网页端没该信息
            headerTemple['x-csrf-token']=Infojson['token']
            cookieStr='_tb_token_=%s' % Infojson['token'] #初始化cookie
        
        for _ in Infojson['cookie']:
            #数据银行的getcookie很有问题!!!并非所有的键值能用用上
            if _['name'] !='_tb_token_':
                cookieStr+=';%s = %s' % (_['name'],_['value'])
        
        headerTemple['cookie']=cookieStr
            
        return headerTemple
    


class HeaderOfAli:
    '''只需要考虑阿里的平台,京东暂时不管
        将selenium获取头和头处理组装的类,其他类去耦合
        最接近主流程的类
        不再定义成员变量,只是其他类的组合实现
        '''
    @staticmethod
    def loginMethod(headerObj,slmObj):
        '''返回字典格式的header
            调用selenium用在两种场景
            1.本地没有文件,2.本地的文件过期
            但即便调用了selemium,也要区分是在已经打开浏览器的情况下用,还是没有的情况'''
        
        #如果有浏览器就调用另一个方法,两种方法参数一样,只是selenium的步骤不一样
        if hasattr(slmObj, 'driver'): 
            loginInfo=slmObj.aliLoginWithDriver(headerObj.platform) 
        else:
            loginInfo=slmObj.aliLoginWithSb(headerObj.platform) 
            
        headerObj.localFileHandle('write',loginInfo) #写入本地
        
        return headerObj.headerOfBroswer(loginInfo)
    
    #方法和其他类耦合
    @staticmethod
    def getHeader(headerObj,slmObj):
        '''slmObj:selenium过程对象
            返回可用的header
            之前写的可读性不好,所有if都并列'''
        #需要加一个判断,slmObj有无driver属性
        #如果第一个header生效了,而第二个没有
        
        if not os.path.exists(headerObj.localPath):#第一次运行直接进selenium
            #也就是说,是要去selenium获取头,但怎么获取放方法中
            return HeaderOfAli.loginMethod(headerObj,slmObj)
        else:#如果本地有
            loginInfo=headerObj.localFileHandle('read') #先从本地拿
            header=headerObj.headerOfBroswer(loginInfo) #用浏览器头拼接
            r2=requests.get(authMap[headerObj.platform],headers=header,proxies={'https':None})#用到了全局变量
            
            #不应该直接就进策略中心,但数据银行和策略中心的header是通用的
            #多一步验证操作
            if r2.text.find('SUCCESS') == -1 :
                return HeaderOfAli.loginMethod(headerObj,slmObj)
            
            return header
    
    @staticmethod
    def getHeaderAll(headerObjList,slmObj,distribute=False):
        '''如果输入列表,就返回列表
            没有哪个地方会用到两种cookie,起码现阶段每个任务都是一个平台对多账号
            从任务/流程做的程序是结果产出导向
            从账号信息做的程序是资源消费导向
            '''
        #有个问题,分发的过程主流程中,也就是说制定了headerObj的路径变量就一定会走存储路线
        return [HeaderOfAli.getHeader(_, slmObj) for _ in headerObjList] 
        



    