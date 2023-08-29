# -*- coding: utf-8 -*-
"""
Created on Tue Jun  6 11:37:33 2023

@author: chenyue
连接数据库,上传数据库
"""
from odps import ODPS
import pandas as pd


class MaxC_DB:  
    
    @staticmethod
    def dataTrans(df=pd.DataFrame(),xlfilePath='',textFormat=False):
        '''
        textFormat 是否是txt格式
        '''
        
        if xlfilePath:
            if textFormat:
                df=pd.read_csv(xlfilePath,sep=',',header=None,encoding='gbk')
            else:
                df=pd.read_excel(xlfilePath)
                
        if not df.empty: #不为空就做变换
            rawData=df.to_dict(orient='index')
            rlt=eval(str(rawData).replace('nan','0').replace('None','0')) #格式转换
            return [list(_.values()) for _ in rlt.values()]
        
        raise Exception('空数据帧不需要上传')
        
    
    @staticmethod
    def odpsInsert(odpsObj,tbName,li):
        '''
        odpsObj odps实例化对象
        tbName 表名
        li 列表套列表的数据
        '''

        t = odpsObj.get_table(tbName) #改maxc的表名
        with t.open_writer() as writer:
            writer.write(li)  # 这里records可以是可迭代对象
    
        print('向表: %s 新增%d行记录项' % (tbName,len(li)))
    
