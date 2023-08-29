# -*- coding: utf-8 -*-
"""
Created on Mon Oct 31 11:22:53 2022

@author: chenyue
"""
#导包
from sqlalchemy import create_engine
import os
from datetime import datetime
'''
使用方法:
  1.定义dbAccount变量,需要账密,库名,端口号
  2.实例化MySQLconn类,需要表名[,主键标识]
  3.MySQLconn对象调用clearAndInsert方法,需要数据帧
  4.控制台查看运行反馈或者本地桌面查看运行日志
'''

#额外的过程
def writeLog(info2Ops):
    '''给实在RPA的单独方法,克服原生python print方法不显示'''
    with open(os.path.join(os.path.expanduser("~"), 'Desktop/adsIndbLog.txt'),'a') as f:
       f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + info2Ops + '\n')

    print(info2Ops)


#定义工具类
class MySQLconn():
    '''数据库操作类,获取信息,上传数据'''

    @classmethod
    def sqlOperate(cls,sqlStr):
        '''使用python执行Mysql语句,无需实例化'''
        with cls.engine.connect() as con:
            rlt=con.execute(sqlStr)
            
        return rlt #可能会返回多种数据类型
            
    def __init__(self,tablename,dbAccount,**kwargs):
        '''
        初始化时要求传入账密信息
        '''
        
        self.tablename=tablename
        self.ds=kwargs.get('ds',None) #删除操作会用到
        MySQLconn.engine = create_engine("mysql+pymysql://%s:%s@%s:%s/%s" %(
                                        dbAccount['user'],
                                        dbAccount['password'],
                                        dbAccount['host'],
                                        dbAccount['port'],
                                        dbAccount['database']),encoding='utf-8')
        
        
        

    def colsIntable(self):
        '''返回表Fields列表'''
        fldRlt=self.sqlOperate('show columns from %s' % self.tablename)
        fieldsList = list(_._data[0] for _ in fldRlt) #整合字段成为列表
        
        return fieldsList
    
    def clearOldData(self,**kwargs):
        '''删除原有数据记录
            ds行使主键功能,常用yyyy-mm-dd格式日期,不绝对
            没有返回值
            如果不传日期,什么也不删,引用处控制'''
        delStr='delete from %s where ds = "%s"' % (self.tablename,self.ds)
        if kwargs:
            for k,v in kwargs.items():
                delStr += ' and %s = "%s"'%(k,v) 
        
        self.sqlOperate(delStr)
        writeLog(self.tablename + ' 数据库删除操作完成')
        
        
    def __dataframeUpload__(self,DataFrame):
        '''上传至数据库,不允许单独使用'''
        DataFrame.to_sql(self.tablename,MySQLconn.engine,if_exists='append', index=False)
        writeLog(self.tablename + ' 数据已上转至数据库,请在网页端进行校验')
        
    def clearAndInsert(self,DataFrame,**kwargs):
        """包含删数据和传数据过程
            精准删除额外条件的数据需要关键词传参"""
        if self.ds:
            self.clearOldData(**kwargs)
            self.__dataframeUpload__(DataFrame)
        else:
            writeLog(self.tablename + ' 什么也没做,实例化请传入ds参数,比如2018-09-12')
            
