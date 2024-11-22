import requests
import pandas as pd
import json
import numpy as np
from datetime import datetime, date
import csv
import time
import ssl
import os
import threading
ssl._create_default_https_context = ssl._create_unverified_context
pd.options.mode.chained_assignment = None  # default='warn'
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

def moving_average(x, w):
    return np.convolve(x, np.ones(w), "valid") / w

def print_log(ss, is_debug):
    if is_debug:
        print(ss)
        
def get_twse_stock_info(df, stock):
    target_data = df[df["股票代號"] == int(stock)]
    name = target_data.iloc[0]['股票名稱']
    priceEarningRatio = target_data.iloc[0]['本益比']
    yieldRatio = target_data.iloc[0]['殖利率(%)']
    priceBookRatio = target_data.iloc[0]['股價淨值比']
    name, priceEarningRatio, yieldRatio, priceBookRatio
    return name, priceEarningRatio, yieldRatio, priceBookRatio

def get_otc_stock_info(df, stock):
    target_data = df[df['SecuritiesCompanyCode'] == stock]
    name = target_data.iloc[0]['CompanyName']
    priceEarningRatio = target_data.iloc[0]['PriceEarningRatio']
    dividendPerShare = target_data.iloc[0]['DividendPerShare']
    yieldRatio = target_data.iloc[0]['YieldRatio']
    priceBookRatio = target_data.iloc[0]['PriceBookRatio']
    name, priceEarningRatio, yieldRatio, priceBookRatio
    return name, priceEarningRatio, yieldRatio, priceBookRatio

def get_twse_stock_db_info():
    link = 'http://www.twse.com.tw/exchangeReport/BWIBBU_ALL?response=open_data'
    df = pd.read_csv(link, encoding='utf_8_sig')
    return df

def get_otc_stock_db_info():
    link = 'http://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis'
    json_data = requests.get(link, verify=False).json()
    df = pd.DataFrame.from_records(json_data)
    return df

def calculate_target_trend(vol_data, pri_data, pri_max_data, debug = False):
    data_min_num = 70
    if len(vol_data) < data_min_num or len(pri_data) < data_min_num:
        # print("Not enough data amount")
        return False
    aa = -7
    bb = -28
    if len(vol_data[bb:aa]) == 0 or len(pri_data[bb:aa]) == 0:
        return False
    if vol_data[bb:aa].mean() == 0:
        return False
    if pri_data[bb:aa].mean() == 0:
        return False
    
    pos_valid = True
    vol_valid = True
    trend_valid = True
    smooth_valid = True
    
    try:
        vol_valid = vol_valid and np.max(vol_data[aa:]) > 1250
        vol_valid = vol_valid and np.mean(vol_data[aa:]) > 800
        
        if not vol_valid:
            print_log("vol invalid", debug)
            return False
        
        pri_cur = pri_data[-1]
        pri_5ma = moving_average(pri_data, 5)
        pri_10ma = moving_average(pri_data, 10)
        pri_20ma = moving_average(pri_data, 20)
        pri_60ma = moving_average(pri_data, 60)
        
        # if pri_5ma[-1] == 0 or pri_10ma[-1] == 0 or pri_20ma[-1] == 0 or pri_60ma[-1] == 0:
        #     return False
        
        # pos_valid = pos_valid and pri_cur / pri_5ma[-1] <= 1.04 and pri_cur / pri_5ma[-1] >= 0.97
        # pos_valid = pos_valid and pri_cur / pri_5ma[-1] <= 1.03 and pri_cur / pri_5ma[-1] >= 0.97
        pos_valid = pos_valid and pri_cur / pri_5ma[-1] <= 1.04 and pri_cur / pri_5ma[-1] >= 1
        print_log("pri_cur / pri_5ma[-1]: %f"%(pri_cur / pri_5ma[-1]), debug and not pos_valid)
        # pos_valid = pos_valid and pri_cur / pri_10ma[-1] <= 1.04 and pri_cur / pri_10ma[-1] >= 0.97
        # pos_valid = pos_valid and pri_cur / pri_10ma[-1] <= 1.03 and pri_cur / pri_10ma[-1] >= 0.97
        pos_valid = pos_valid and pri_cur / pri_10ma[-1] <= 1.04 and pri_cur / pri_10ma[-1] >= 0.992
        print_log("pri_cur / pri_10ma[-1]: %f"%(pri_cur / pri_10ma[-1]), debug and not pos_valid)
        # pos_valid = pos_valid and pri_5ma[-1] / pri_10ma[-1] <= 1.04 and pri_5ma[-1] / pri_10ma[-1] >= 0.975
        # pos_valid = pos_valid and pri_5ma[-1] / pri_10ma[-1] <= 1.032 and pri_5ma[-1] / pri_10ma[-1] >= 0.974
        pos_valid = pos_valid and pri_5ma[-1] / pri_10ma[-1] <= 1.032 and pri_5ma[-1] / pri_10ma[-1] >= 0.98
        print_log("pri_5ma[-1] / pri_10ma[-1]: %f"%(pri_5ma[-1] / pri_10ma[-1]), debug and not pos_valid)
        # pos_valid = pos_valid and pri_10ma[-1] / pri_20ma[-1] <= 1.06 and pri_10ma[-1] / pri_20ma[-1] >= 0.98
        # pos_valid = pos_valid and pri_10ma[-1] / pri_20ma[-1] <= 1.045 and pri_10ma[-1] / pri_20ma[-1] >= 0.974
        pos_valid = pos_valid and pri_10ma[-1] / pri_20ma[-1] <= 1.09 and pri_10ma[-1] / pri_20ma[-1] >= 0.974
        print_log("pri_10ma[-1] / pri_20ma[-1]: %f"%(pri_10ma[-1] / pri_20ma[-1]), debug and not pos_valid)
        # pos_valid = pos_valid and pri_cur / pri_20ma[-1] <= 1.07 and pri_cur / pri_20ma[-1] >= 0.99
        pos_valid = pos_valid and pri_cur / pri_20ma[-1] <= 1.12 and pri_cur / pri_20ma[-1] >= 0.995
        print_log("pri_cur / pri_20ma[-1]: %f"%(pri_cur / pri_20ma[-1]), debug and not pos_valid)
        # pos_valid = pos_valid and pri_10ma[-1] / pri_60ma[-1] >= 1.04
        # pos_valid = pos_valid and pri_10ma[-1] / pri_60ma[-1] >= 1.022
        pos_valid = pos_valid and pri_10ma[-1] / pri_60ma[-1] >= 1.028
        print_log("pri_10ma[-1] / pri_60ma[-1]: %f"%(pri_10ma[-1] / pri_60ma[-1]), debug and not pos_valid)
        
        if not pos_valid:
            print_log("pos invalid", debug)
            return False
        
        trend_valid = trend_valid and pri_10ma[-1] / pri_10ma[-5] >= 0.99
        print_log("pri_10ma[-1] / pri_10ma[-5]: %f"%(pri_10ma[-1] / pri_10ma[-5]), debug and not trend_valid)
        # trend_valid = trend_valid and pri_20ma[-1] / pri_20ma[-8] >= 0.985
        trend_valid = trend_valid and pri_20ma[-1] / pri_20ma[-8] >= 1.055
        print_log("pri_20ma[-1] / pri_20ma[-8]: %f"%(pri_20ma[-1] / pri_20ma[-8]), debug and not trend_valid)
        # trend_valid = trend_valid and pri_60ma[-1] / pri_60ma[-10] >= 1.035
        # trend_valid = trend_valid and pri_60ma[-1] / pri_60ma[-10] >= 1.023
        trend_valid = trend_valid and pri_60ma[-1] / pri_60ma[-10] >= 1.028
        print_log("pri_60ma[-1] / pri_60ma[-10]: %f"%(pri_60ma[-1] / pri_60ma[-10]), debug and not trend_valid)
        
        if not trend_valid:
            print_log("trend invalid", debug)
            return False
        
        smooth_valid = smooth_valid and pri_data[-1] / pri_data[-2] > 0.955
        smooth_valid = smooth_valid and pri_data[-1] / pri_data[-8:].max() > 0.96
        smooth_valid = smooth_valid and pri_data[-1] / pri_max_data[-9:].max() > 0.94
        print_log("pri_data[-1] / pri_max_data[-10:]: %f"%(pri_data[-1] / pri_max_data[-8:].max()), debug and not smooth_valid)
        
        if not smooth_valid:
            print_log("smooth invalid", debug)
            return False
        
        # print(pri_cur / pri_5ma[-1], pri_cur / pri_10ma[-1], pri_5ma[-1] / pri_10ma[-1], pri_10ma[-1] / pri_20ma[-1], pri_cur / pri_20ma[-1] ,pri_10ma[-1] / pri_60ma[-1])
        # print(pri_20ma[-1] / pri_20ma[-8], pri_60ma[-1] / pri_60ma[-10])
    except:
        # print("?")
        return False
    # print(vol_valid , pos_valid , trend_valid)
    return vol_valid and pos_valid and trend_valid and smooth_valid

def calculate_target_bear_trend(vol_data, pri_data, pri_max_data, debug = False):
    data_min_num = 70
    if len(vol_data) < data_min_num or len(pri_data) < data_min_num:
        # print("Not enough data amount")
        return False
    aa = -7
    bb = -28
    if len(vol_data[bb:aa]) == 0 or len(pri_data[bb:aa]) == 0:
        return False
    if vol_data[bb:aa].mean() == 0:
        return False
    if pri_data[bb:aa].mean() == 0:
        return False
    
    pos_valid = True
    vol_valid = True
    trend_valid = True
    smooth_valid = True
    
    try:
        vol_valid = vol_valid and np.max(vol_data[aa:]) > 450
        
        if not vol_valid:
            print_log("vol invalid", debug)
            return False
        
        pri_cur = pri_data[-1]
        pri_5ma = moving_average(pri_data, 5)
        pri_10ma = moving_average(pri_data, 10)
        pri_20ma = moving_average(pri_data, 20)
        pri_60ma = moving_average(pri_data, 60)
        
        # if pri_5ma[-1] == 0 or pri_10ma[-1] == 0 or pri_20ma[-1] == 0 or pri_60ma[-1] == 0:
        #     return False
        
        # pos_valid = pos_valid and pri_cur / pri_5ma[-1] <= 1.04 and pri_cur / pri_5ma[-1] >= 0.97
        # pos_valid = pos_valid and pri_cur / pri_5ma[-1] <= 1.03 and pri_cur / pri_5ma[-1] >= 0.97
        pos_valid = pos_valid and pri_cur / pri_5ma[-1] <= 1.017 and pri_cur / pri_5ma[-1] >= 0.96
        print_log("pri_cur / pri_5ma[-1]: %f"%(pri_cur / pri_5ma[-1]), debug and not pos_valid)
        # pos_valid = pos_valid and pri_cur / pri_10ma[-1] <= 1.04 and pri_cur / pri_10ma[-1] >= 0.97
        # pos_valid = pos_valid and pri_cur / pri_10ma[-1] <= 1.03 and pri_cur / pri_10ma[-1] >= 0.97
        pos_valid = pos_valid and pri_cur / pri_10ma[-1] <= 1.011 and pri_cur / pri_10ma[-1] >= 0.96
        print_log("pri_cur / pri_10ma[-1]: %f"%(pri_cur / pri_10ma[-1]), debug and not pos_valid)
        # pos_valid = pos_valid and pri_5ma[-1] / pri_10ma[-1] <= 1.04 and pri_5ma[-1] / pri_10ma[-1] >= 0.975
        # pos_valid = pos_valid and pri_5ma[-1] / pri_10ma[-1] <= 1.032 and pri_5ma[-1] / pri_10ma[-1] >= 0.974
        pos_valid = pos_valid and pri_5ma[-1] / pri_10ma[-1] <= 1.02 and pri_5ma[-1] / pri_10ma[-1] >= 0.968
        print_log("pri_5ma[-1] / pri_10ma[-1]: %f"%(pri_5ma[-1] / pri_10ma[-1]), debug and not pos_valid)
        # pos_valid = pos_valid and pri_10ma[-1] / pri_20ma[-1] <= 1.06 and pri_10ma[-1] / pri_20ma[-1] >= 0.98
        # pos_valid = pos_valid and pri_10ma[-1] / pri_20ma[-1] <= 1.045 and pri_10ma[-1] / pri_20ma[-1] >= 0.974
        pos_valid = pos_valid and pri_10ma[-1] / pri_20ma[-1] <= 1.026 and pri_10ma[-1] / pri_20ma[-1] >= 0.91
        print_log("pri_10ma[-1] / pri_20ma[-1]: %f"%(pri_10ma[-1] / pri_20ma[-1]), debug and not pos_valid)
        # pos_valid = pos_valid and pri_cur / pri_20ma[-1] <= 1.07 and pri_cur / pri_20ma[-1] >= 0.99
        pos_valid = pos_valid and pri_cur / pri_20ma[-1] <= 1.005 and pri_cur / pri_20ma[-1] >= 0.88
        print_log("pri_cur / pri_20ma[-1]: %f"%(pri_cur / pri_20ma[-1]), debug and not pos_valid)
        # pos_valid = pos_valid and pri_10ma[-1] / pri_60ma[-1] >= 1.04
        # pos_valid = pos_valid and pri_10ma[-1] / pri_60ma[-1] >= 1.022
        pos_valid = pos_valid and pri_10ma[-1] / pri_60ma[-1] <= 0.913
        print_log("pri_10ma[-1] / pri_60ma[-1]: %f"%(pri_10ma[-1] / pri_60ma[-1]), debug and not pos_valid)
        
        if not pos_valid:
            print_log("pos invalid", debug)
            return False
        
        trend_valid = trend_valid and pri_10ma[-1] / pri_10ma[-5] <= 1.015
        print_log("pri_10ma[-1] / pri_10ma[-5]: %f"%(pri_10ma[-1] / pri_10ma[-5]), debug and not trend_valid)
        # trend_valid = trend_valid and pri_20ma[-1] / pri_20ma[-8] >= 0.985
        trend_valid = trend_valid and pri_20ma[-1] / pri_20ma[-8] <= 1.008
        print_log("pri_20ma[-1] / pri_20ma[-8]: %f"%(pri_20ma[-1] / pri_20ma[-8]), debug and not trend_valid)
        # trend_valid = trend_valid and pri_60ma[-1] / pri_60ma[-10] >= 1.035
        # trend_valid = trend_valid and pri_60ma[-1] / pri_60ma[-10] >= 1.023
        trend_valid = trend_valid and pri_60ma[-1] / pri_60ma[-10] <= 0.919
        print_log("pri_60ma[-1] / pri_60ma[-10]: %f"%(pri_60ma[-1] / pri_60ma[-10]), debug and not trend_valid)
        
        if not trend_valid:
            print_log("trend invalid", debug)
            return False
        
        smooth_valid = smooth_valid and pri_data[-1] / pri_data[-2] < 1.045
        smooth_valid = smooth_valid and pri_data[-1] / pri_data[-8:].max() < 1.04
        smooth_valid = smooth_valid and pri_data[-1] / pri_max_data[-9:].max() < 1.06
        print_log("pri_data[-1] / pri_max_data[-10:]: %f"%(pri_data[-1] / pri_max_data[-8:].max()), debug and not smooth_valid)
        
        if not smooth_valid:
            print_log("smooth invalid", debug)
            return False
        
        # print(pri_cur / pri_5ma[-1], pri_cur / pri_10ma[-1], pri_5ma[-1] / pri_10ma[-1], pri_10ma[-1] / pri_20ma[-1], pri_cur / pri_20ma[-1] ,pri_10ma[-1] / pri_60ma[-1])
        # print(pri_20ma[-1] / pri_20ma[-8], pri_60ma[-1] / pri_60ma[-10])
    except:
        # print("?")
        return False
    # print(vol_valid , pos_valid , trend_valid)
    return vol_valid and pos_valid and trend_valid and smooth_valid

def get_stock_history(stock, db_path, start_date, input_date, duration):
    stock_info_file_path = os.path.join(db_path, "%s.csv"%(stock))
    if not os.path.isfile(stock_info_file_path):
        return None
    df_all = pd.read_csv(stock_info_file_path)
    if start_date is not None:
        df_all = df_all[df_all["日期"] >= start_date]
        df_all = df_all.iloc[0:duration]
    elif input_date is not None:
        df_all = df_all[df_all["日期"] <= input_date]
        df_all = df_all.iloc[-duration:]
    else:
        df_all = df_all.iloc[-duration:]
    return df_all
# get_stock_history(2357, start_date=None, end_date="113/10/07", duration=80)

def analyze_stock(isOtc, data_list_path, target_list, input_date, db_path, thread_total = 1, thread_idx = 0):
    # if isOtc:
    #     df = get_otc_stock_db_info()
    #     # data_path = r".\db\otc.csv"
    # else:
    #     df = get_twse_stock_db_info()
    #     # data_path = r".\db\twse.csv"
    
    data_path = data_list_path

    stock_list = []
    with open(data_path, newline='', encoding='utf_8_sig') as csvfile:
        line_list = csv.reader(csvfile)
        for line in line_list:
            stock_list.append(line[0])
    
    stock_list_len = len(stock_list)
    thread_item_num = np.ceil(stock_list_len / thread_total)
    idx_start = thread_item_num * thread_idx
    idx_end = idx_start + thread_item_num
    if thread_idx == thread_total - 1: # last thread
        idx_end = stock_list_len
    
    # target_list = []

    for stock in stock_list[int(idx_start):int(idx_end)]:
        # vol_data, pri_data, pri_max_data, df_all = get_time_duration_stock_info(time_data, stock, min_volumn=150, ma_num=1, isOtc=isOtc)
        
        # get stock history
        # stock_info_file_path = os.path.join(db_path, "%s.csv"%(stock))
        # if not os.path.isfile(stock_info_file_path):
        #     continue
        # df_all = pd.read_csv(stock_info_file_path)
        
        df_all = get_stock_history(stock, db_path, start_date=None, input_date=input_date, duration=100)
        # print(df_all.head)
        # break
        
        date_data = df_all['日期'].values
        vol_data = df_all['成交張數'].values
        pri_data = df_all['收盤價'].values
        pri_max_data = df_all['最高價'].values
        pri_min_data = df_all['最低價'].values
        pri_sta_data = df_all['開盤價'].values
        
        if vol_data is None or pri_data is None:
            continue
        valid = calculate_target_trend(vol_data, pri_data, pri_max_data)
        # valid = calculate_target_bear_trend(vol_data, pri_data, pri_max_data)
        if valid:
            name, priceEarningRatio, yieldRatio, priceBookRatio = "", "", "", ""
            if isOtc:
                #name, priceEarningRatio, yieldRatio, priceBookRatio = get_otc_stock_info(df, stock)
                target_list.append([date_data[-1], stock, name, priceEarningRatio, yieldRatio, priceBookRatio, pri_data[-1], pri_max_data[-1], pri_min_data[-1], pri_sta_data[-1], 1])
                # print(stock, name, priceEarningRatio, yieldRatio, priceBookRatio, pri_data[-1], 1)
            else:
                #name, priceEarningRatio, yieldRatio, priceBookRatio = get_twse_stock_info(df, stock)
                target_list.append([date_data[-1], stock, name, priceEarningRatio, yieldRatio, priceBookRatio, pri_data[-1], pri_max_data[-1], pri_min_data[-1], pri_sta_data[-1], 0])
                # print(stock, name, priceEarningRatio, yieldRatio, priceBookRatio, pri_data[-1], 0)
        # break
        
def price_tick_refine(price):
    if price < 10: # 0.01
        price = np.round(price, 2)
    elif price < 50: # 0.05
        price = np.round(price*2, 1)/2
    elif price < 100: # 0.1
        price = np.round(price, 1)
    elif price < 500: # 0.5
        price = np.round(price*2, 0)/2
    elif price < 1000: # 1
        price = np.round(price, 0)
    else: # 5
        price = np.round(price*2, -1)/2
    return price

def get_takeProfit_stopLoss(price, min_price, max_price, isLong):
    takeProfit_ratio = 6
    stopLoss_ratio = 3
    buy_in_up_ratio = 2
    buy_in_down_ratio = 1.5
    if isLong:
        takeProfit_price = price * (1. + takeProfit_ratio/100)
        stopLoss_price = price * (1. - stopLoss_ratio/100)
        buy_in_up_price = price * (1. + buy_in_up_ratio/100)
        buy_in_down_price = price * (1. - buy_in_down_ratio/100)
    else:
        takeProfit_price = price * (1. - takeProfit_ratio/100)
        stopLoss_price = price * (1. + stopLoss_ratio/100)
        buy_in_up_price = price * (1. + buy_in_down_ratio/100)
        buy_in_down_price = price * (1. - buy_in_up_ratio/100)
    return price_tick_refine(takeProfit_price), price_tick_refine(stopLoss_price), price_tick_refine(buy_in_up_price), price_tick_refine(buy_in_down_price)

# def tp_sl_cal(stock, buy_price, tp, sl, cur_price_min, cur_price_max, cur_price_start):
#     # Take profit & Stop loss calculator
#     status = 0 # 1: Take Profit, 2: Stop Loss
#     ror = 0 # rate of return
#     sell_price = 0
    
#     if cur_price_start <= sl: # stop loss
#         status = 2
#         sell_price = cur_price_start
#     elif cur_price_min <= sl:
#         status = 2
#         sell_price = sl
#     elif cur_price_start >= tp: # take profit
#         status = 1
#         sell_price = cur_price_start
#     elif cur_price_max >= tp:
#         status = 1
#         sell_price = tp
        
#     ror = (sell_price - buy_price) / buy_price * 100.
#     if status != 0:
#         print(stock, status, ror, sell_price)
        
def select_stock(twse_list_path, otc_list_path, input_date, db_path, pool_cur_path):
    target_list_twse = []
    analyze_stock(isOtc = False, data_list_path = twse_list_path, target_list = target_list_twse, input_date = input_date, db_path = db_path, thread_total = 1, thread_idx = 0)
    target_list_otc = []
    analyze_stock(isOtc = True, data_list_path = otc_list_path, target_list = target_list_otc, input_date = input_date, db_path = db_path, thread_total = 1, thread_idx = 0)

    target_list = target_list_twse + target_list_otc
    df_select = pd.DataFrame(target_list, columns=['Date', 'Stock', 'Name', 'PE', 'Yield', 'PB', 'Price', 'Max Price', 'Min Price', 'Start Price', 'isOTC'])
    
    if os.path.isfile(pool_cur_path): # already exist some stocks in pool
        df_pool = pd.read_csv(pool_cur_path)
        for index, row in df_pool.iterrows():
            stock = str(row['Stock'])
            if stock in df_select['Stock'].values:
                df_select = df_select.drop(df_select[df_select['Stock'] == stock].index)
            # else:
            #     print(stock)
            #     # df_select.loc[len(df_select)] = row
            #     df_select = df_select._append(row, ignore_index = True)
        df_select = df_select.reset_index(drop=True)
    return df_select

def tp_sl_calculate(df_select, target_path):
    target_final_list = []
    for index, row in df_select.iterrows():
        input_date = row["Date"]
        stock = row["Stock"]
        price = row["Price"]
        max_price = row["Max Price"]
        min_price = row["Min Price"]
        isOtc = row["isOTC"]
        takeProfit_price, stopLoss_price, buy_in_up_price, buy_in_down_price = get_takeProfit_stopLoss(price, min_price, max_price, True)
        # print(target[5], takeProfit_price, stopLoss_price)
        target_final_list.append([input_date, stock, takeProfit_price, stopLoss_price, buy_in_up_price, buy_in_down_price, isOtc])

    df_target = pd.DataFrame(target_final_list, columns=['Date', 'Stock', 'Take Profit', 'Stop Loss', 'Buy In Up', 'Buy In Down', 'isOTC'])
    df_target.to_csv(target_path, encoding='utf-8-sig')
    return df_target

# def settlement(target_path, db_path, input_date):
#     df_target = pd.read_csv(target_path)
#     for index, row in df_target.iterrows():
#         stock = str(int(row['Stock']))
#         tp = row['Take Profit']
#         sl = row['Stop Loss']
#         buy_up = row['Buy In Up']
#         buy_down = row['Buy In Down']
#         buy_price = (buy_up + buy_down) / 2
#         cur_info = get_stock_history(stock, db_path, start_date=None, input_date=input_date, duration=1)
#         # print(cur_date)
#         cur_date = cur_info.iloc[0]['日期']
#         cur_vol = cur_info.iloc[0]['成交張數']
#         cur_price = cur_info.iloc[0]['收盤價']
#         cur_price_max = cur_info.iloc[0]['最高價']
#         cur_price_min = cur_info.iloc[0]['最低價']
#         cur_price_start = cur_info.iloc[0]['開盤價']
        
#         tp_sl_cal(stock, buy_price, tp, sl, cur_price_min, cur_price_max, cur_price_start)

def tp_sl_cal(stock, buy_price, tp, sl, cur_price_min, cur_price_max, cur_price_start):
    # Take profit & Stop loss calculator
    status = 0 # 1: Take Profit, 2: Stop Loss
    ror = 0 # rate of return
    sell_price = 0
    
    if cur_price_start <= sl: # stop loss
        status = 2
        sell_price = cur_price_start
    elif cur_price_min <= sl:
        status = 2
        sell_price = sl
    elif cur_price_start >= tp: # take profit
        status = 1
        sell_price = cur_price_start
    elif cur_price_max >= tp:
        status = 1
        sell_price = tp
        
    ror = (sell_price - buy_price) / buy_price * 100.
    if status != 0 and (sell_price == 0 or abs(ror) >= 13):
        status = -1
    return status, stock, ror, sell_price
        
def settlement(df_position, db_path, input_date, pool_cur_path, pool_path, out_path):
    # df_target = pd.read_csv(position_path)
    data = {'Date': [], 'Stock': [], 'Take Profit': [], 'Stop Loss':[], 'Buy Price':[], 'isOTC':[]}
    df_pool = pd.DataFrame(data)
    data = {'Date': [], 'Date Out': [], 'Stock': [], 'RoR': [], 'Buy Price':[], 'Sell Price':[], 'Status':[], 'isOTC':[]}
    df_out = pd.DataFrame(data)
    
    for index, row in df_position.iterrows():
        stock_date = row['Date']
        stock = str(int(row['Stock']))
        tp = row['Take Profit']
        sl = row['Stop Loss']
        buy_price = row['Buy Price']
        isOTC = row['isOTC']
        cur_info = get_stock_history(stock, db_path, start_date=None, input_date=input_date, duration=1)
        # print(cur_date)
        cur_date = cur_info.iloc[0]['日期']
        if cur_date == stock_date:
            status = 0
        else:        
            cur_vol = cur_info.iloc[0]['成交張數']
            cur_price = cur_info.iloc[0]['收盤價']
            cur_price_max = cur_info.iloc[0]['最高價']
            cur_price_min = cur_info.iloc[0]['最低價']
            cur_price_start = cur_info.iloc[0]['開盤價']
            status, stock, ror, sell_price = tp_sl_cal(stock, buy_price, tp, sl, cur_price_min, cur_price_max, cur_price_start)
        
        if status == -1:
            # print(cur_date, stock, ror)
            continue
        elif status == 0:
            data = {'Date': stock_date, 'Stock': stock, 'Take Profit': tp, 'Stop Loss':sl, 'Buy Price':buy_price, 'isOTC':isOTC}
            df_pool.loc[len(df_pool)] = data
        else: # stop loss or take profit
            data = {'Date': stock_date, 'Date Out': cur_date, 'Stock': stock, 'RoR': ror, 'Buy Price':buy_price, 'Sell Price':sell_price, 'Status':status, 'isOTC':isOTC}
            df_out.loc[len(df_out)] = data
        # break
    df_pool.to_csv(pool_cur_path, encoding='utf-8-sig')
    df_pool.to_csv(os.path.join(pool_path, input_date.replace('/', '') + ".csv"), encoding='utf-8-sig')
    df_out.to_csv(os.path.join(out_path, input_date.replace('/', '') + ".csv"), encoding='utf-8-sig')
    
    return df_pool, df_out

def sim_buy(target_analyze_path):
    df_position = pd.read_csv(target_analyze_path)
    # print(df_target.head)
    data_list = []
    for index, row in df_position.iterrows():
        stock = str(int(row['Stock']))
        stock_date = row['Date']
        buy_date = stock_date # TODO
        tp = row['Take Profit']
        sl = row['Stop Loss']
        buy_up = row['Buy In Up']
        buy_down = row['Buy In Down']
        isOTC = row['isOTC']
        buy_price = (buy_up + buy_down) / 2
        buy_price = price_tick_refine(buy_price)
        data_list.append([buy_date, stock, tp, sl, buy_price, isOTC])
    df_buy = pd.DataFrame(data_list, columns=['Date', 'Stock', 'Take Profit', 'Stop Loss', 'Buy Price', 'isOTC'])
    # df_position.to_csv(position_path, encoding='utf-8-sig')
    return df_buy

def get_stock_position(df_buy, position_path, pool_cur_path):
    if os.path.isfile(pool_cur_path): # already exist some stocks in pool
        df_pool = pd.read_csv(pool_cur_path)
        df_position = pd.concat([df_buy, df_pool], axis=0)
        df_position = df_position.reset_index(drop=True)
        df_position.to_csv(position_path, encoding='utf-8-sig')
        return df_position
    else:
        df_buy.to_csv(position_path, encoding='utf-8-sig')
        return df_buy

def add_date_to_string(input_date):
    yy = int(input_date.split('/')[0])
    mm = int(input_date.split('/')[1])
    dd = int(input_date.split('/')[2])
    dd = dd + 1
    if dd > 31:
        dd = 1
        mm = mm + 1
    if mm > 12:
        mm = 1
        yy = yy + 1
    output_date = str(yy) + "/" + str(mm).zfill(2) + "/" + str(dd).zfill(2)
    return output_date