 
from flask import Flask, jsonify, request
import random
import numpy as np
import scipy
from scipy import stats
import pymongo
from pymongo import MongoClient

 
app = Flask(__name__)


client = MongoClient()
# print(client.list_database_names())
portfolio_sims_db = client["portfolio_sims"]
sims_col = portfolio_sims_db["sims"]
 
@app.route("/sim", methods=['GET'])
def sim():

    username = request.args.get("username")
    portfolio_name = request.args.get("portfolio_name")
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


    stock_val_nominal_list = [ [] for _ in range(horizon)]
    stock_val_real_list = [ [] for _ in range(horizon)]
    bond_val_nominal_list = [ [] for _ in range(horizon)]
    bond_val_real_list = [ [] for _ in range(horizon)]
    cash_val_nominal_list = [ [] for _ in range(horizon)]
    cash_val_real_list = [ [] for _ in range(horizon)]
    inflation_list = [ [] for _ in range(horizon)]
    portfolio_nominal_list = [ [] for _ in range(horizon)] 
    portfolio_real_list =  [ [] for _ in range(horizon)]

    for sim in range(num_sims):

        stock_val_nominal = user_stocks * principal
        stock_val_real = user_stocks * principal
        bond_val_nominal = user_bonds * principal
        bond_val_real = user_bonds * principal
        cash_val_nominal = user_cash * principal
        cash_val_real = user_cash * principal

        portfolio_val_nominal = principal
        portfolio_val_real = principal

        start_cash = cash_val_nominal
        start_stock = stock_val_nominal
        start_bond = bond_val_nominal
        
        for x in range(horizon):
            
        
            inflation = random.gauss(inflation_rate, inflation_std)
            if inflation == -1:
                inflation = -.99999


            stock_return_rate = random.gauss(stock_ret, stock_std)
            stock_returns = stock_val_nominal * stock_return_rate
            stock_div_ret = stock_val_nominal * stock_div
            

            stock_val_nominal += stock_returns

            if reinvest == True:
                # print("reinvesting stocks")
                stock_val_nominal += stock_div_ret
            else:
                # print("not reinvesting stocks")
                cash_val_nominal += stock_div_ret


            
            real_stock_ret_rate = ((1 + stock_return_rate) / (1 + inflation)) - 1
            real_stock_returns = stock_val_nominal * real_stock_ret_rate

            stock_val_real += real_stock_returns

            
            # BONDS
            bond_return_rate = random.gauss(bond_ret, bond_std)
            # print(f"stock ret rate: {stock_return_rate}")
            bond_returns = bond_val_nominal * bond_return_rate
            # print(f"stock rets: {stock_returns}")
            bond_div_ret = bond_val_nominal * bond_div
            # print(f"stock div ret: {stock_div_ret}")

            bond_val_nominal += bond_returns

            if reinvest == True:
                # print("reinvesting bonds")
                bond_val_nominal += bond_div_ret
            else:
                # print("not reinvesting bonds")
                cash_val_nominal += bond_div_ret

            
            real_bond_ret_rate = ((1 + bond_return_rate) / (1 + inflation)) - 1
            real_bond_returns = bond_val_nominal * real_bond_ret_rate
            

            bond_val_real += real_bond_returns

            
                
            nominal_cash_returns = cash_val_nominal - start_cash

            if abs(nominal_cash_returns) == 0:
                real_cash_returns = (cash_val_nominal * (1 - inflation)) - start_cash
            else:
                if start_cash != 0:
                    nominal_cash_ret_rate = (cash_val_nominal / start_cash) - 1
                    real_cash_ret_rate = ((1 + nominal_cash_ret_rate) / (1 + inflation)) - 1
                    real_cash_returns = (start_cash * (1 + real_cash_ret_rate)) - start_cash
                else:
                    real_cash_returns = (nominal_cash_returns * (1 - inflation)) 

            
            cash_val_real += real_cash_returns

            portfolio_val_nominal = (cash_val_nominal + stock_val_nominal + bond_val_nominal)

            portfolio_val_real = (cash_val_real + stock_val_real + bond_val_real)

            start_cash = cash_val_nominal

            stock_val_nominal_list[x].append(stock_val_nominal)
            stock_val_real_list[x].append(stock_val_real)
            bond_val_nominal_list[x].append(bond_val_nominal)
            bond_val_real_list[x].append(bond_val_real)
            cash_val_nominal_list[x].append(cash_val_nominal)
            cash_val_real_list[x].append(cash_val_real)
            inflation_list[x].append(inflation)

            portfolio_nominal_list[x].append(portfolio_val_nominal)
            portfolio_real_list[x].append(portfolio_val_real)

    sim_results = {

    "stock_vals_nominal": stock_val_nominal_list,
    "stock_vals_real": stock_val_real_list,
    "bond_vals_nominal": bond_val_nominal_list,
    "bond_vals_real": bond_val_real_list,
    "cash_vals_nominal": cash_val_nominal_list,
    "cash_vals_real": cash_val_real_list,
    "Inflation": inflation_list,
    "portfolio_vals_nominal":  portfolio_nominal_list,
    "portfolio_vals_real":  portfolio_real_list,

    }
    
    try:
        sims_col.update_one( {"username" : username, "portfolio_name" : portfolio_name }, 
                {"$set": sim_results}, upsert=True)
        results = {"success": 1}
    except:
        results = {"success": 0, "error_msg": "Something has gone wrong"}
    
    return jsonify({"results": results})


@app.route("/check-sim", methods=['GET'])
def check_sim():

    username = request.args.get("username")
    portfolio_name = request.args.get("portfolio_name")

    sim_run = sims_col.find_one({"username": username, "portfolio_name": portfolio_name})
    
    if not sim_run:
        error_msg = "No simulation has been run on this portfolio"
        results = {"success": 0, "error_msg": error_msg}
    else:
        results = {"success": 1}

    return jsonify({"results": results})




if __name__ == "__main__":
    app.run(port=8001, debug=True)