#!/usr/bin/env python
# coding: utf-8

# In[1]:


import time
import pyupbit
import datetime
import pandas as pd
import numpy as np
import warnings

from scipy.signal import savgol_filter
#from scipy.signal import savitzky_golay

#import matplotlib.pyplot as plt


# In[2]:


pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)


# In[3]:


warnings.filterwarnings(action='ignore')   # 경고 메시지 비활성화, 활성화시엔 action=default 으로 설정


# In[4]:


access_key = "eziU49y9cSYp6BFEu8Vu8yEwk0AAZIxn1o0ya7Bp"
secret_key = "mjkWq13cmg1XE38l9xK7x80XhcIsyChHrmyx3IVe"

upbit = pyupbit.Upbit(access_key, secret_key)


# In[5]:


check_currency = 'KRW'

candle_count = 77
candle_type = '5min'

avg_duration_1 = 5
avg_duration_2 = 15

coin_target = ['KRW-BTC', 'KRW-ETH', 'KRW-NEO', 'KRW-LTC', 'KRW-ETC', 'KRW-OMG', 'KRW-WAVES', 'KRW-QTUM', 'KRW-LSK', 'KRW-REP', 'KRW-SBD', 'KRW-BTG', 'KRW-BCH']

series_1_cnt_No = 5
series_1_cnt_buy_cri = 2
#series_1_cnt_sell_cri = 2

filt_c_a_buy_cri = 1.00005
filt_c_a_sell_cri = 1

invest_ratio = 0.015   # 보유 금액의 최대 몇 % 를 투자할것인가 (예> 0.1 <-- 보유금액 10% 투자) 

#buy_time_value = 2
#sell_time_value = 1
#idle_time_value = 0

sell_one_candle_force = 0.03   # 강제 매도 하락율
transaction_fee_ratio = 0.0005   # 거래 수수료 비율

time_factor = 9   # 클라우드 서버와 한국과의 시차


if candle_type == '1min' :
    candle_adapt = 'minute1'
    time_unit = 1
elif candle_type == '3min' :
    candle_adapt = 'minute3'
    time_unit = 3
elif candle_type == '5min' :
    candle_adapt = 'minute5'
    time_unit = 5
elif candle_type == '10min' :
    candle_adapt = 'minute10'
    time_unit = 10
elif candle_type == '15min' :
    candle_adapt = 'minute15'
    time_unit = 15
elif candle_type == '30min' :
    candle_adapt = 'minute30'
    time_unit = 30
elif candle_type == '60min' :
    candle_adapt = 'minute60'
    time_unit = 60
elif candle_type == '240min' :
    candle_adapt = 'minute240'
    time_unit = 240


# In[6]:


tickers = pyupbit.get_tickers()

LIST_coin_KRW = []

for i in range (0, len(tickers), 1):
    if tickers[i][0:3] == 'KRW':
        LIST_coin_KRW.append(tickers[i])
        
LIST_check_coin_currency = []

for i in range (0, len(LIST_coin_KRW), 1):
    LIST_check_coin_currency.append(LIST_coin_KRW[i][4:])


    
LIST_check_coin_currency_2 = []

for i in range (0, len(LIST_check_coin_currency), 1) :
    temp = 'KRW-' + LIST_check_coin_currency[i]
    LIST_check_coin_currency_2.append(temp)


# In[7]:


# 잔고 조회, 현재가 조회 함수 정의

def get_balance(target_currency):   # 현급 잔고 조회
    """잔고 조회"""
    balances = upbit.get_balances()   # 통화단위, 잔고 등이 Dictionary 형태로 balance에 저장
    for b in balances:
        if b['currency'] == target_currency:   # 화폐단위('KRW', 'KRW-BTC' 등)에 해당하는 잔고 출력
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_balance_locked(target_currency):   # 거래가 예약되어 있는 잔고 조회
    """잔고 조회"""
    balances = upbit.get_balances()   # 통화단위, 잔고 등이 Dictionary 형태로 balance에 저장
    for b in balances:
        if b['currency'] == target_currency:   # 화폐단위('KRW', 'KRW-BTC' 등)에 해당하는 잔고 출력
            if b['locked'] is not None:
                return float(b['locked'])
            else:
                return 0
    return 0

def get_avg_buy_price(target_currency):   # 거래가 예약되어 있는 잔고 조회
    """평균 매수가 조회"""
    balances = upbit.get_balances()   # 통화단위, 잔고 등이 Dictionary 형태로 balance에 저장
    for b in balances:
        if b['currency'] == target_currency:   # 화폐단위('KRW', 'KRW-BTC' 등)에 해당하는 잔고 출력
            if b['avg_buy_price'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 0
    return 0


def get_current_price(invest_coin):
    """현재가 조회"""
    #return pyupbit.get_orderbook(tickers=invest_coin)[0]["orderbook_units"][0]["ask_price"]
    return pyupbit.get_current_price(invest_coin)

#price = pyupbit.get_current_price("KRW-BTC")


# In[8]:


def moving_avg_trend (DF_input) :
    Series_moving_avg_1 = DF_input['close'].rolling(window = avg_duration_1).mean()
    Series_moving_avg_2 = DF_input['close'].rolling(window = avg_duration_2).mean()
    
    DF_moving_avg_1 = Series_moving_avg_1.to_frame(name='close_avg_1')
    DF_moving_avg_2 = Series_moving_avg_2.to_frame(name='close_avg_2')
    
    DF_moving_avg_1['prior_close_avg_1'] = DF_moving_avg_1['close_avg_1'].shift(1)
    DF_moving_avg_1['ma_ratio_1'] = DF_moving_avg_1['close_avg_1'] / DF_moving_avg_1['prior_close_avg_1']
    
    DF_moving_avg_2['prior_close_avg_2'] =  DF_moving_avg_2['close_avg_2'].shift(1)
    DF_moving_avg_2['ma_ratio_2'] = DF_moving_avg_2['close_avg_2'] / DF_moving_avg_2['prior_close_avg_2']
    
    DF_input['prior_close'] = DF_input['close'].shift(1)
    DF_input['ratio_close'] = DF_input['close'] / DF_input['prior_close']
    DF_input['prior_ratio_close'] = DF_input['ratio_close'].shift(1)
    DF_input['now_m_prior_ratio_close'] = DF_input['ratio_close'] / DF_input['prior_ratio_close']
    
    DF_input['a_candle_after_ratio'] = DF_input['ratio_close'].shift(-1)
    
    DF_input['close_m_open'] = DF_input['close'] - DF_input['open']
    DF_input['close_to_open_ratio'] = DF_input['close'] / DF_input['open']
    
    DF_input['vol_ratio'] = DF_input['volume'] / DF_input['volume'].mean()
                                                                     
    
    DF_concat = pd.concat([DF_input,DF_moving_avg_1],axis=1)
    DF_concat = pd.concat([DF_concat,DF_moving_avg_2],axis=1)
    
    DF_concat['ma1_m_ma2'] = DF_concat['close_avg_1'] - DF_concat['close_avg_2']
    DF_concat['multiple'] = DF_concat['ratio_close'] * DF_concat['ma_ratio_1'] * DF_concat['ma_ratio_2']
    
    interim_close_avg_1 = DF_concat.iloc[avg_duration_1:]['close_avg_1'].values   # 첫번째 이동평균선에서, 초기 이동평균선 구하는 count만큼 NaN인 부분 제외
    DF_concat['sg_filter_close_avg1'] = 0   # savgol_filter가 적용된 값을 구하기 위한 열 생성
    interim_sg_filtered = savgol_filter(interim_close_avg_1, 51, 3)
    
    for k in range (avg_duration_1, len(DF_concat['close_avg_1']), 1) :
        DF_concat['sg_filter_close_avg1'][k] = interim_sg_filtered[k - avg_duration_1]   # avg_duration_1만큼 shift되어 적용되므로, interim_sg_filtered의 첫번째 값 부터 적용하기 위해 avg_duration_1만큼 빼서 반영
        
        DF_concat['pri_sg_filter_close_avg1'] = DF_concat['sg_filter_close_avg1'].shift(1)
        DF_concat['ratio_pri_now_sg_filter_close_avg1'] = DF_concat['sg_filter_close_avg1'] / DF_concat['pri_sg_filter_close_avg1']   # 이번 값을 이전값으로 나누어, 얼마나 수치가 변했는지 비율로 판단
        
        DF_check = DF_concat.iloc[(avg_duration_1 + 1) :][['open', 'close', 'close_avg_1','sg_filter_close_avg1', 'close_avg_2', 'pri_sg_filter_close_avg1', 'ratio_pri_now_sg_filter_close_avg1']]   #초기 이동평균선을 구하느라 NaN이 뜨는 열을 제외
        
        DF_check['filter_bin'] = [1 if k > 1 else 0 for k in DF_check['ratio_pri_now_sg_filter_close_avg1']]   # ratio_pri_now_sg_filter_close_avg1 깂이 1보다 크면 'filter_bin'을 1로 설정
        
        DF_check['series_1_count'] = 0   # 'filter_bin'이 0/1인 경우(ratio_pri_now_sg_filter_close_avg1)가 최근 N개 window에서 몇개나 있었는가? <--- 0이 기준값 이상으로 연속적인 상황에서 1로 변환된(상승세로 전환) 순간에 매수하기 위함
        #DF_check['inv_qual'] = 0   # invesestable_qualified 여부를 판단하기 위한 열
        #buy_state = 0
        
        for m in range (series_1_cnt_No, len(DF_check['filter_bin']), 1) :
            DF_check['series_1_count'][m] = DF_check.iloc[(m - series_1_cnt_No) : m]['filter_bin'].sum()   # 최근 'seires_1_con_No' 만큼 동안 이동평균선 비율의 상승(1) / 하락(0)을 count
    
    return DF_check


# In[9]:


bought_state = 0
bought_coin = 'KRW-BTC'


# In[10]:


while True:
    
    now = datetime.datetime.now() + datetime.timedelta(seconds = (time_factor * 3600))   # 클라우드 서버와 한국과의 시간차이 보정 (9시간)
    print ('bought_state : {0}   / now : {1}'.format(bought_state, now))
    
    if (now.minute % time_unit == 0) & (52 < (now.second % 60) <= 57) :   # N시:00:02초 ~ N시:00:07초 사이 시각이면
        balances2 = upbit.get_balances()
        print ('current_aseet_status\n', balances2)
        
        if bought_state == 0 :   # 매수가 없는 상태라면
            for coin_i in coin_target :
                time.sleep(1)
                print ('\n [[[[[[[[[[[[ coin ]]]]]]]]]] :', coin_i)
                DF_inform = pyupbit.get_ohlcv(coin_i, count = candle_count, interval = candle_adapt)
                DF_mov_avg_info = moving_avg_trend (DF_inform)
                print ('DF_mov_avg_info\n :', DF_mov_avg_info)
                print('filt_c_a_buy_cri : {0}  / ratio_pri_now_sg_filter_close_avg1[-2] : {1}'.format(filt_c_a_buy_cri, DF_mov_avg_info['ratio_pri_now_sg_filter_close_avg1'][-2]))
                print('series_1_cnt_buy_cri : {0} / series_1_count[-2] : {1}'.format(series_1_cnt_buy_cri, DF_mov_avg_info['series_1_count'][-2]))
                

                # 매수 영역
                if ((DF_mov_avg_info['ratio_pri_now_sg_filter_close_avg1'][-2] >= filt_c_a_buy_cri) & (DF_mov_avg_info['series_1_count'][-2] <= series_1_cnt_buy_cri)) :
                    print ('$$$$$ [{0}] buying_transaction is coducting $$$$$'.format(coin_i))
                
                    investable_budget = get_balance(check_currency) * invest_ratio
                    #bought_volume = (investable_budget * (1 - transaction_fee_ratio)) / get_current_price(coin_i)
                
                    transaction_buy = upbit.buy_market_order(coin_i, investable_budget)   # 시장가로 매수
                    # transaction_buy = upbit.buy_limit_order(bought_coin, bought_price, bought_volume)
                    time.sleep(10)
                    print ('buy_transaction_result :', transaction_buy)
                    print ('time : {0}  /  bought_target_volume : {1}  /  bought_volume_until_now : {2}'.format((datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))), bought_volume, get_balance(coin_i[4:])))
                    bought_coin = coin_i
                
                    #bought_price = get_balance(coin_i[4:])['avg_buy_price']
                    for o in range(0, len(upbit.get_balances()), 1) :
                        if upbit.get_balances()[o]['currency'] == coin_i[4:] :
                            bought_price =  int(upbit.get_balances()[o]['avg_buy_price'])
                    print ('bought_price : ', bought_price)
                
                
                    bought_state = 1
                    
                
        # 매도 영역
        if bought_state == 1 :   # 매수가 되어 있는 상태라면
            print ('\nnow :', (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))))
            print ('\n bought_state : {0}  [[[[[[[[[[[[ coin___{1} selling condition checking]]]]]]]]]] :'.format(bought_state, bought_coin))
            DF_inform = pyupbit.get_ohlcv(bought_coin, count = candle_count, interval = candle_adapt)
            DF_mov_avg_info_2 = moving_avg_trend (DF_inform)
            print ('DF_mov_avg_info_2\n :', DF_mov_avg_info_2)
            print ('filt_c_a_sell_cri : {0}  / ratio_pri_now_sg_filter_close_avg1[-2] : {1}'.format(filt_c_a_sell_cri, DF_mov_avg_info_2['ratio_pri_now_sg_filter_close_avg1'][-2]))
            print ('series_1_cnt_No : {0}  / series_1_count[-2] : {1}'.format(series_1_cnt_No, DF_mov_avg_info_2['series_1_count'][-2]))
                                
            if ((DF_mov_avg_info_2['ratio_pri_now_sg_filter_close_avg1'][-2] <= filt_c_a_sell_cri) & (DF_mov_avg_info_2['series_1_count'][-2] == series_1_cnt_No)) :
                                
                transaction_sell = upbit.sell_market_order(bought_coin, get_balance(bought_coin[4:]))   # 시장가에 매도
                time.sleep(5)
                print ('\nnow :', (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))))
                print ('sell_transaction_result :', transaction_sell)
                
                bought_state = 0
                
                time.sleep(5)
        
        
        # 하락시 강제 매도 영역
        if bought_state == 1 :   # 매수가 되어 있는 상태라면
            
            if get_current_price(bought_coin) <= (upbit.get_balances()[1]['avg_buy_price'] * (1-sell_one_candle_force)) :   # 강제 매도 가격 이하로 현재가격이 하락하게 되면
                transaction_sell = upbit.sell_market_order(coin_i, get_balance(coin_i[4:0]))   # 시장가에 매도
                time.sleep(5)
                print ('\nnow :', (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))))
                print ('sell_transaction_result :', transaction_sell)
                bought_state = 0
                time.sleep(5)
        
    time.sleep(1)
    


# In[ ]:


'''
while True :
    
    now = datetime.datetime.now() + datetime.timedelta(seconds = (time_factor * 3600))   # 클라우드 서버와 한국과의 시간차이 보정 (9시간)
    print ('now :', now)
    
    # 매수 영역
    if (bought_state == 0) & ((now.minute % time_unit == 0) & (52 < (now.second % 60) <= 57)) :   # N시 : time_unit : 52초 ~ N시 : time_unit : 57초 사이 시각이면
        
        print ('current_aseet_status\n', upbit.get_balances())
        
        for coin_i in LIST_coin_candi :
            print ('\n [[[[[[[[[[[[ coin ]]]]]]]]]] :', coin_i)
            DF_inform = pyupbit.get_ohlcv(coin_i, count = candle_count, interval = candle_adapt)
            print ('DF_target :\n', DF_inform)
            DF_mov_avg = moving_avg_trend (DF_inform)
            print ('DF_mov_avg :\n', DF_mov_avg)
                        
            if ((DF_mov_avg['ratio_close'][-2] >= ratio_close_cri) & \
            (DF_mov_avg['now_m_prior_ratio_close'][-2] >= now_m_prior_ratio_close_cri) & \
            (DF_mov_avg['ma_ratio_1'][-2] >= ma_ratio_1_cri) & \
            (DF_mov_avg['ma_ratio_2'][-2] >= ma_ratio_2_cri) & \
            (DF_mov_avg['ma1_m_ma2'][-2] >= ma1_m_ma2_cri) & \
            (DF_mov_avg['multiple'][-2] >= multiple_cri) & \
            (DF_mov_avg['vol_ratio'][-2] >= vol_ratio_cri)) :
                
                print ('$$$$$ [{0}] buying_transaction is coducting $$$$$'.format(coin_i))
                
                investable_budget = get_balance(check_currency) * invest_ratio
                #bought_volume = (investable_budget * (1 - transaction_fee_ratio)) / get_current_price(coin_i)
                
                transaction_buy = upbit.buy_market_order(coin_i, investable_budget)   # 시장가로 매수
                # transaction_buy = upbit.buy_limit_order(bought_coin, bought_price, bought_volume)
                time.sleep(10)
                print ('buy_transaction_result :', transaction_buy)
                print ('time : {0}  /  bought_target_volume : {1}  /  bought_volume_until_now : {2}'.format((datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))), bought_volume, get_balance(coin_i[4:])))
                
                #bought_price = get_balance(coin_i[4:])['avg_buy_price']
                for k in range(0, len(upbit.get_balances()), 1) :
                    if upbit.get_balances()[k]['currency'] == coin_i[4:] :
                        bought_price =  int(upbit.get_balances()[k]['avg_buy_price'])
                print ('bought_price : ', bought_price)
                bought_state = 1
                
                # 매도 영역
                while ((datetime.datetime.now().minute % time_unit) < (time_unit -1)) :
                    if get_current_price(coin_i) >= (bought_price * (1 + sell_auto + transaction_fee_ratio)) :   # 자동 매도 가격보다 현재가격이 상승하게되면 
                        transaction_sell = upbit.sell_market_order(coin_i, get_balance(coin_i[4:]))   # 시장가에 매도
                        print ('\nnow :', (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))))
                        print ('sell_transaction_result :', transaction_sell)
                        bought_state = 0
                        
                        break   # 자동 매도 완료시 while 문 탈출
                                                     
                                                     
                    if get_current_price(coin_i) <= bought_price * (1-sell_one_candle_force) :   # 강제 매도 가격 이하로 현재가격이 하락하게 되면
                            transaction_sell = upbit.sell_market_order(coin_i, get_balance(coin_i[4:0]))   # 시장가에 매도
                            print ('\nnow :', (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))))
                            print ('sell_transaction_result :', transaction_sell)
                            bought_state = 0
                            
                            break   # 강제 매도시 while 문 탈출
                    
                    time.sleep(5)
                
                transaction_sell = upbit.sell_market_order(coin_i, get_balance(coin_i[4:0]))   # 한 time_unit내에 자동 또는 강제 매도가 안되어, 시장가에 매도
                print ('\nnow :', (datetime.datetime.now() + datetime.timedelta(seconds = (time_factor*3600))))
                print ('sell_transaction_result :', transaction_sell)
                bought_state = 0
                
            time.sleep(1)
            
    time.sleep(1)
                


# In[ ]:





# In[ ]:





# In[ ]:


'''
def simulate_coin (coin_inv) :
    print('[[[[[ coin : {0} ]]]]]'.format(coin_inv))
    DF_test = pyupbit.get_ohlcv(coin_inv, count = candle_count, interval = candle_adapt)
    DF_test_ma = moving_avg_trend (DF_test)
    
    interim_close_avg_1 = DF_test_ma.iloc[avg_duration_1:]['close_avg_1'].values   # 초기 이동평균선 구하는 count만큼 NaN인 부분 제외
    DF_test_ma['sg_filter_close_avg1'] = 0
    interim_sg_filter_c_avg1 = savgol_filter(interim_close_avg_1, 51, 3)
    
    for i in range (avg_duration_1, len(DF_test_ma['close_avg_1']), 1) :
        DF_test_ma['sg_filter_close_avg1'][i] = interim_sg_filter_c_avg1[i - avg_duration_1]
        
    DF_test_ma['pri_sg_filter_close_avg1'] = DF_test_ma['sg_filter_close_avg1'].shift(1)
    DF_test_ma['ratio_pri_now_sg_filter_close_avg1'] = DF_test_ma['sg_filter_close_avg1'] / DF_test_ma['pri_sg_filter_close_avg1'] 
        
    DF_check = DF_test_ma.iloc[(avg_duration_1 + 1) :][['open', 'close', 'close_avg_1','sg_filter_close_avg1', 'close_avg_2', 'pri_sg_filter_close_avg1', 'ratio_pri_now_sg_filter_close_avg1']]
        
    DF_check['filter_bin'] = [1 if i > 1 else 0 for i in DF_check['ratio_pri_now_sg_filter_close_avg1']]
    DF_check['series_1_count'] = 0
    DF_check['inv_qual'] = 0
    buy_state = 0
        
    for k in range (series_1_cnt_No, len(DF_check['filter_bin']), 1) :
        DF_check['series_1_count'][k] = DF_check.iloc[(k - series_1_cnt_No) : k]['filter_bin'].sum()
            
    for m in range (series_1_cnt_No, len(DF_check['series_1_count']), 1) :
        if ((DF_check['ratio_pri_now_sg_filter_close_avg1'][m] >= filt_c_a_buy_cri) & (DF_check['series_1_count'][m] <= series_1_cnt_buy_cri) & (buy_state == 0)) :
            DF_check['inv_qual'][m] = buy_time_value
            buy_state = 1
            
        elif ((DF_check['ratio_pri_now_sg_filter_close_avg1'][m] <= filt_c_a_sell_cri) & (DF_check['series_1_count'][m] == series_1_cnt_No) & (buy_state == 1)) :
            DF_check['inv_qual'][m] = sell_time_value
            buy_state = 0
                
        else :
            DF_check['inv_qual'][m] = idle_time_value
    

    bought_state = 0
    bought_volume = 0
    test_money = 1000000
    #price = 0 
    residual_value = 1000000
    
    for i in range (0, len(DF_check), 1) :
        if ((bought_state == 0) & (DF_check['inv_qual'][i] == buy_time_value)) :
            bought_volume = (test_money / DF_check['open'][i]) * (1 - transaction_fee_ratio)
            test_money = 0
            bought_state = 1
            residual_value = DF_check['open'][i] * bought_volume
            print ('in_BUY_state___residual_value : ', residual_value)
            
        elif ((bought_state == 1) & (DF_check['inv_qual'][i] == sell_time_value)) :
            test_money = (bought_volume * DF_check['open'][i]) * (1 - transaction_fee_ratio)
            bought_volume = 0
            bought_state = 0
            residual_value = test_money
            print ('in_SELL_state___residual_value : ', residual_value)
    
'''


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




