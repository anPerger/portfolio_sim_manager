 
from flask import Flask, jsonify, request
import random
import numpy as np
import scipy
from scipy import stats
import pymongo
from pymongo import MongoClient

 
app = Flask(__name__)



 
@app.route("/sim", methods=['GET'])
def sim():

    user_stocks = float(request.args.get("user_stocks"))
    user_bonds = float(request.args.get("user_bonds"))
    user_cash = float(request.args.get("user_cash"))

    stock_ret = float(request.args.get("stock_ret"))
    stock_std = float(request.args.get("stock_std"))
    stock_div = float(request.args.get("stock_div"))

    bond_ret = float(request.args.get("bond_ret"))
    bond_std = float(request.args.get("bond_std"))
    bond_div = float(request.args.get("bond_div"))

    inflation_rate = float(request.args.get("inflation_rate"))
    inflation_std = float(request.args.get("inflation_std"))
    horizon = int(request.args.get("user_horizon"))
    num_sims = int(request.args.get("sims"))
    principal = float(request.args.get("principal"))
    reinvest_str = request.args.get("reinvest")

    if reinvest_str == "True":
        reinvest = True
    else:
        reinvest = False

    print(reinvest)
    print(type(reinvest))
  
    # print(f"user_stocks: {user_stocks}")
    # print(f"user_bonds: {user_bonds}")
    # print(f"user_cash: {user_cash}")

    # print(f"stock_ret: {stock_ret}")
    # print(f"stock_std: {stock_std}")
    # print(f"stock_div: {stock_div}")
    
    # print(f"bond_ret: {bond_ret}")
    # print(f"bond_std: {bond_std}")
    # print(f"bond_div: {bond_div}")

    # print(f"inflation_rate: {inflation_rate}")
    # print(f"inflation_std: {inflation_std}")
    # print(f"horizon: {horizon}")
    # print(f"num_sims: {num_sims}")
    # print(f"principal: {principal}")
    # print(f"reinvest: {reinvest}")

    

    
    results_list = []

    for sim in range(num_sims):

        stock_val = user_stocks * principal
        bond_val = user_bonds * principal
        cash_val = user_cash * principal
        
        results = {}
        
        for x in range(1, horizon + 1):
            
        
            inflation = random.gauss(inflation_rate, inflation_std)


            stock_return_rate = random.gauss(stock_ret, stock_std)
            stock_returns = stock_val * stock_return_rate
            stock_div_ret = stock_val * stock_div
            

            stock_val += stock_returns

            if reinvest == True:
                print("reinvesting stocks")
                stock_val += stock_div_ret
            else:
                print("not reinvesting stocks")
                cash_val += stock_div_ret


            real_stock_ret_rate = ((1 + stock_return_rate) / (1 + inflation)) - 1
            real_stock_returns = stock_val * real_stock_ret_rate


            stock_preformance = {
                "nominal_stock_return_rate":  stock_return_rate,
                "nominal_stock_returns": stock_returns,
                "real_stock_return_rate": real_stock_ret_rate,
                "real_stock_returns": real_stock_returns,
                "stock_dividend_returns": stock_div_ret,
                "stock_val": stock_val,
            }
            
            # BONDS
            bond_return_rate = random.gauss(bond_ret, bond_std)
            # print(f"stock ret rate: {stock_return_rate}")
            bond_returns = bond_val * bond_return_rate
            # print(f"stock rets: {stock_returns}")
            bond_div_ret = bond_val * bond_div
            # print(f"stock div ret: {stock_div_ret}")

            bond_val += bond_returns

            if reinvest == True:
                print("reinvesting bonds")
                bond_val += bond_div_ret
            else:
                print("not reinvesting bonds")
                cash_val += bond_div_ret


            real_bond_ret_rate = ((1 + bond_return_rate) / (1 + inflation)) - 1
            real_bond_returns = bond_val * real_bond_ret_rate


            bond_preformance = {
                "nominal_bond_return_rate":  bond_return_rate,
                "nominal_bond_returns": bond_returns,
                "real_bond_return_rate": real_bond_ret_rate,
                "real_bond_returns": real_bond_returns,
                "bond_dividend_returns": bond_div_ret,
                "bond_val": bond_val,
            }

            print(f"cash val: {cash_val}")

            results[f"year_{x}"] = {
                "inflation": inflation,
                "stocks": stock_preformance,
                "bonds": bond_preformance,
                "cash": cash_val
                }
            
        results_list.append(results)



    return jsonify({"results": results_list})

if __name__ == "__main__":
    app.run(port=8001, debug=True)