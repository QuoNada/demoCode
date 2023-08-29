#构建一些全局变量,可以解决跨年问题
#变量名尽可能不变
'''
导出日期变量,统一字符串格式
    last_month_first_day_str
    last_month_end_day_str
    lastMonthNumber
    last_month_30_day_str
    ly_lm_first_day
    ll_month_last_day

---备用---
#上个月的月份名称
lastMonthNumber=(today_now.replace(day=1)-timedelta(days=1)).month
'''
from datetime import datetime,timedelta


def undefineLast():
    m=(today_now.replace(day=1)-timedelta(days=1)).month
    if m ==2:#返回最后一天
        return (today_now.replace(day=1)-timedelta(days=1)).strftime('%Y%m%d')
    else:#返回第30号
        return (today_now.replace(day=1)-timedelta(days=1)).replace(day=30).strftime('%Y%m%d')


today_now = datetime.today()
# today_now = datetime(2023,5,5) #调用日期,datetime格式,一定不能错!!!!
yesterday_str=(today_now-timedelta(days=1)).strftime('%Y%m%d')
#上个月1号,8为数字字串格式
last_month_first_day_str=(today_now.replace(day=1)-timedelta(days=1)).replace(day=1).strftime('%Y%m%d') #上个月第一天,datetime格式
#上个月最后一天
last_month_end_day_str=(today_now.replace(day=1)-timedelta(days=1)).strftime('%Y%m%d')


#上个月最后一天,数字格式
lm_ld_Number=(today_now.replace(day=1)-timedelta(days=1)).day


#上个月的28,29,30
last_month_30_day_str=undefineLast()
#去年,上个月的1号;使用相对时间
#比如2023-01-05的要产生2021-12-01的结果
#先做年份加减,再置换成1号做月份替换,最后置换成1号成为上个月的
ly_lm_first_day=(today_now.replace(year=today_now.year-1,day=1)-timedelta(days=1)).replace(day=1).strftime('%Y%m%d') #上个月第一天,datetime格式
#去年,上个月的最后一天
ly_lm_end_day=(today_now.replace(year=today_now.year-1,day=1)-timedelta(days=1)).strftime('%Y%m%d')
#今年上上个月的最后一天
ll_month_last_day=((today_now.replace(day=1)-timedelta(days=1)).replace(day=1)-timedelta(days=1)).strftime('%Y%m%d') #上个月第一天,datetime格式

#上上个月的最后一天
last2_month_end_day_str=(((today_now.replace(day=1)-timedelta(days=1)).replace(day=1))-timedelta(days=1)).strftime('%Y%m%d')

#2022年写死,不灵活
strat_2022='20220101'
end_2022='20221231'


#
