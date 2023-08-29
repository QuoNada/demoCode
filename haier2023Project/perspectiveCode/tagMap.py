# -*- coding: utf-8 -*-
"""
Created on Tue May  9 13:57:14 2023

@author: chenyue
和业务需要耦合严重,直接把路径写死
用的地方实在是太多了,虽然brand3做了重构,但涉及到其他业务脚本的应用,所以新的需求临时跨项目用
    PECHOINProject/clsPack/card_temple_crowd.py

只是方便本地的标签统计,作为准备阶段应用,生产阶段用其他地方的东西
"""
import json
import os

from os import path

repoPath = path.dirname(path.dirname(path.dirname(__file__)))


def mapBuild(mode):
    '''构建英文_中文的3级映射'''
    # 先准备1级标签,基本是死的
    lv1Map = {'BasicTag': '基础标签',
              'IndusTag': '行业标签',
              'LifeTag': '生活方式',
              'FunPerferTag': '娱乐偏好',
              'ExclusiveTag': '专属标签'
              }

    tagDir = path.join(repoPath, r'haier2023Project\perspectiveCode\tag')
    # 再准备2级标签
    tagMap_enk = {}
    tagLv3_id = {}
    for _ in os.listdir(tagDir):
        lv1TagName = lv1Map[_.split('.')[0]]
        with open(path.join(tagDir, _), 'r', encoding='utf-8') as f:
            # 有两种文件
            jsonf = json.load(f)
            for li1 in jsonf['data']:  # li1是字典
                tagLv3_id[li1['tagCateId']] = li1['tagCateName']
                # 都有data键,lv1可遍历内容很少
                for li2 in li1['tagPropList']:  # 只要li2的两个键
                    tagMap_enk[li2['tagId']] = '_'.join((lv1TagName, li1['tagCateName'], li2['tagTitle']))

    # 按参数返回两种映射关系
    if mode == 'lv4_detail':
        return tagMap_enk
    elif mode == 'lv3_id':
        return tagLv3_id


# 其他脚本直接引用变量
# 不做简易映射,主流程调用要给全面的标签信息
tagMap_enk = mapBuild('lv4_detail')
tagMap_zhk = {v: k for k, v in tagMap_enk.items()}

idMap_idk = mapBuild('lv3_id')
idMap_namek = {v: k for k, v in idMap_idk.items()}
