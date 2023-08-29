# -*- coding: utf-8 -*-

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

class SLMlogin:
    '''selenium操作'''
    
    driver=None
    
    def __init__(self,account='', password=''):
        '''实例化对象可以调用类属性,driver'''
        self.account=account
        self.password=password

    
    @staticmethod
    def __driverSet__():
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
        SLMlogin.driver=driver
        
        return driver
    
    def __sendAccPw__(self,driver):
        '''传递账号密码,如果网络差iframe不一定能能加载出来'''
        try:
            driver.find_element(by=By.ID,value='fm-login-id').send_keys(self.account)
            driver.find_element(by=By.ID,value='fm-login-password').send_keys(self.password)
            driver.find_element(by=By.CLASS_NAME,value='fm-btn').click() #登录
        except NoSuchElementException:
            driver.refresh()
            return False
    
    
    def __dragSlideBlock__(self,driver):
        '''拖动滑块,基本都能成功,验证不算复杂'''
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
    
    def __queryTokenCookie__(self,driver):
        '''加载主页后获取header信息'''
        #拿到cookie和token,在另一个类里组装到头里
        token=driver.find_element(by=By.XPATH,value=
            '/html/head/meta[@name="_csrf"]').get_attribute('token')
        
        cookie=driver.get_cookies()
        
        return {'token':token,'cookie':cookie}
    

    def aliLoginWithSb(self,platfrom):
        '''运行selenium,返回cookie+token
            包含对滑块的处理
            可能需要人值守
            platfrom 策略中心/数据银行
            '''
        driver=self.__driverSet__()
        
        #新增加的内容
        if platfrom=='数据银行':
            driver.get('https://databank.tmall.com/')
            iframe=driver.find_element(by=By.CLASS_NAME,value='login-iframe')
        elif platfrom=='策略中心':
            driver.get('https://strategy.tmall.com/')
            iframe=driver.find_element(by=By.ID,value='tbLoginFrame')
        
        driver.switch_to.frame(iframe) #内嵌iframe
        
        if self.__sendAccPw__(driver) == False:
            #如果失败,会刷新网页,需要人工介入
            #已经介入人工了,没必要再往下走了,提早返回,拿header只是第一步
            input('请手动输入账密,进入主页后回车')
            return self.__queryTokenCookie__(driver)
            
        #不稳定,对使用者要求太高
        wait=WebDriverWait(driver,10) #设置等待机制,限时10s操作
        try:
            #如果wait报错,就不会findelement报错
            element=wait.until(EC.visibility_of_all_elements_located(
                    (By.CSS_SELECTOR,'.fm-button.fm-submit.password-login.fm-button-disabled'))) #进入策略中心
            
            #如果登录不能点,就要拖动滑块
            if not driver.find_element(by=By.CSS_SELECTOR,value='.fm-button.fm-submit.password-login.fm-button-disabled').is_selected():
                self.__dragSlideBlock__(driver) #也可能会失败
            else:
                element.cilck()
            
            element=wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR,'.primary-button.turn-databank-btn'))) #进入策略中心
            element.click()
        except TimeoutError:
            input('登录主页后回车')
        #看到主页内容之前可能要好一会,但只要有加载行为就足够了,不需要真的看到内容
        
        return self.__queryTokenCookie__(driver)


#这是一个完全独立的类,用到selenium是一个可能性
#但一定涉及本地的IO和登录的校验是一定的,至于信息的获取还没考虑到那一步
#使用者不关心本地是不是有现成的json,他只有确定的平台,账号密码
    
class HeaderResolve:
    '''头文件的本地读写+验证'''
    
    authMap={
        '数坊':'https://4a.jd.com/datamill/api/common/actionAuth',
        '策略中心':'https://strategy.tmall.com/api/checkDataBankAuth?'
        }
    
    
    headerTemple={
            "user_agent":
                "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
            'content-type': 'application/json'
            }
    
    
        
    def __init__(self,localPath):
        '''和本地的json文件对应,如果没有就创建'''
        self.localPath=localPath
        
    def headerCombine(self,Infojson):
        '''维持原生格式,cookie存在列表中,token存在字串中
            不应该分开,全部来源都是json
            可能来自selenium,可能来自本地
            参数越少越容易用'''
        
        self.headerTemple['cookie']=self.cookieTrans(Infojson['cookie'])
        if Infojson.get('token',False):#数坊网页端没该信息
            self.headerTemple['x-csrf-token']=Infojson['token']
        
        return self.headerTemple
    
    
    def setLocalFile(self,localPath,loginInfo,combine=False):
        '''保存到本地,指定路径,指定存的内容
            内容形式是字典
            '''
        with open(localPath,'w') as f:
            json.dump(loginInfo,f)
        
        #保存的来源基本为selenuium,就不用hr再做额外的拼接了
        if combine:
            return self.headerCombine(loginInfo)
            
    
    #京东数坊可以手动保存可用cookie,但为了统一还是统一用selenium拿,毕竟不是高频需要
    #以现实最小的可能性做基准
    #还需要提前返回
    def localFileRead(self):
        '''如果本地不存在什么也不做
            只读取而不赋值,不拼接'''
        if os.path.exists(self.localPath):
            with open(self.localPath,'r',encoding='utf-8') as f:
                content=json.load(f)
            return content
        
        #文件不存在返回空,直接进入selenium过程
        return
    
    @staticmethod
    def cookieTrans(cookieList):
        '''传入json,python里是list,只能来自selenium
            字典转字串,适用于loginInfo中cookie的值'''
        return ';'.join(['%s = %s' % (_['name'],_['value']) for _ in cookieList])
    
    
    #方法和其他类耦合
    def getHeader(self,platfrom,SLMlogin):
        '''platform:数坊,策略中心
            SLMlogin:selenium过程对象
            返回可用的header'''
        self.headerType=SLMlogin.account
        
        if not os.path.exists(self.localPath):#第一次运行直接进selenium
            loginInfo=SLMlogin.aliLoginWithSb(platfrom)
            header=self.setLocalFile(self.localPath, loginInfo,combine=True)
            return header

        loginInfo=self.localFileRead() #先从本地拿
        if loginInfo:
            header=self.headerCombine(loginInfo)
            r2=requests.get(self.authMap[platfrom],headers=header)
            
            
        #不应该直接就进策略中心,但数据银行和策略中心的header是通用的
        if r2.text.find('SUCCESS') == -1 :
            loginInfo=SLMlogin.aliLoginWithSb(platfrom)
            header=self.setLocalFile(self.localPath, loginInfo,combine=True)
        
        return header

    
    
    
    