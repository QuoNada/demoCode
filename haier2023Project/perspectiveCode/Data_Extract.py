# -*- coding: utf-8 -*-
"""
不够内聚,没有专门的数据库操作类
数据来自数据库
    从画像相关的依赖里找解析的依据
"""
from os import path

repoPath = path.dirname(path.dirname(path.dirname(__file__)))  # 定义项目路径

import sys

sys.path.append(repoPath)

from haier2023Project.perspectiveCode.tagMap_v3 import tagMap_db_all, tagMap_st_casarte
from PECHOINProject.clsPack.Web_Interact import WebQuery
from haier2023Project.Result.Header.HeaderGet import brandMap, header_get

import pandas as pd
import json

platform_Map = {
    '数据银行': tagMap_db_all,
    '策略中心': tagMap_st_casarte
}


def crowdCntGet_plt(WebQueryObj, crowd_id):
    # 不同平台查询的响应不太一样

    if WebQueryObj.platform == '数据银行':
        return WebQueryObj.singleIdQuery_cnt(crowd_id)['data']
    elif WebQueryObj.platform == '策略中心':
        return WebQueryObj.singleIdQuery_cnt(crowd_id)['data']['count']


# 比较靠近顶层,一些规则写死问题不大
def expandPerspective_st(dataList, plt):
    '''
    核心是标签,放在卡片类中好一些
    目的是一行拆多行
    默认双头
    和数据库的结构耦合了
    '''

    wiH = WebQuery(header_get('brand1', plt), plt)
    wiC = WebQuery(header_get('brand2', plt), plt)

    dfList = []
    for _ in dataList:  # 每个_是元组,相当于数据库的一条记录
        tmp = json.loads(_[5])  # 根据json提取数据,耦合点
        tagRate = {}

        # 策略中心不该拼接,和数银统一,到外面再拆
        # 特殊情况,有点重复了,results 加s!
        if tmp['body'].get('results'):  # results的列表不为空
            for k, v in tmp['body']['results'][0]['results'].items():
                for li3 in v['perspectiveItems']:  # 不定数量,li3是字典
                    lvStart = platform_Map[plt]['tagMap_enk'][k]
                    tagDetail = '_'.join((lvStart, li3['tagValueName']))  # 补充n级标签
                    tagRate[tagDetail] = [lvStart, li3['tagValueName'], li3['rate']]  # 无论数银要不要拆分后都保留
        else:
            continue

        # else : # 不确定,待测试,先统一跳过
        #     for k,v in tmp['body'].items():
        #         for li3 in v['perspectiveItems']: #不定数量,li3是字典
        #             tagDetail='_'.join((platform_Map[plt]['tagMap_enk'][k],li3['tagValueName'])) #补充n级标签
        #             tagRate[tagDetail]=li3['rate']

        # 做数据帧的处理,从_抽比例和id
        dfTemp = pd.DataFrame.from_dict(tagRate, orient='index')
        dfTemp.reset_index(inplace=True)
        dfTemp.columns = ['标签明细', '标签1', '标签2', '占比']
        dfTemp['人群id'] = _[3]

        # 头的分别应用,和数银不一样,但是账号可作为最准确的标识
        if str(_).find(brandMap['brand1']['account']) != -1:
            dfTemp['人群包人数'] = crowdCntGet_plt(wiH, crowd_id=_[3])
        elif str(_).find(brandMap['brand2']['account']) != -1:
            dfTemp['人群包人数'] = crowdCntGet_plt(wiC, crowd_id=_[3])

        dfTemp.eval('人数=占比 * 人群包人数 / 100', inplace=True)
        dfTemp['人数'] = dfTemp['人数'].astype(int)

        dfList.append(dfTemp)

    return dfList


def expandPerspective_db(dataList):
    '''
    目的是一行拆多行
    默认是数据银行,默认双头
    和数据库的结构耦合了
    '''
    # 准备头
    plt = '数据银行'
    wiH = WebQuery(header_get('brand1', plt), plt)
    wiC = WebQuery(header_get('brand2', plt), plt)

    dfList = []
    for _ in dataList:  # 每个_是元组,相当于数据库的一条记录
        tmp = json.loads(_[5])  # 根据json提取数据
        tagRate = {}

        if tmp['body'].get('results'):  # 特殊情况,有点重复了,results 加s!
            for k, v in tmp['body']['results'][0]['results'].items():
                for li3 in v['perspectiveItems']:  # 不定数量,li3是字典
                    tagDetail = '_'.join((platform_Map[plt]['tagMap_enk'][k], li3['tagValueName']))  # 补充3级标签
                    tagRate[tagDetail] = li3['rate']
        else:
            for k, v in tmp['body'].items():
                for li3 in v['perspectiveItems']:  # 不定数量,li3是字典
                    tagDetail = '_'.join((platform_Map[plt]['tagMap_enk'][k], li3['tagValueName']))  # 补充3级标签
                    tagRate[tagDetail] = li3['rate']

        # 做数据帧的处理,从_抽比例和id
        dfTemp = pd.DataFrame.from_dict(tagRate, orient='index')
        dfTemp.reset_index(inplace=True)
        dfTemp.columns = ['标签明细', '占比']
        dfTemp['人群id'] = _[3]

        # 头的分别应用
        if str(_).find('brand1') != -1:
            dfTemp['人群包人数'] = wiH.singleIdQuery_cnt(_[3])['data']
        elif str(_).find('brand2') != -1:
            dfTemp['人群包人数'] = wiC.singleIdQuery_cnt(_[3])['data']

        dfTemp.eval('人数=占比 * 人群包人数 / 100', inplace=True)
        dfTemp['人数'] = dfTemp['人数'].astype(int)

        dfList.append(dfTemp)

    return dfList
