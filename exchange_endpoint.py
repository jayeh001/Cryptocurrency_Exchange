from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only
from datetime import datetime
import math
import sys
import traceback

# TODO: make sure you implement connect_to_algo, send_tokens_algo, and send_tokens_eth
from send_tokens import connect_to_algo, connect_to_eth, send_tokens_algo, send_tokens_eth

from models import Base, Order, TX, Log
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

""" Pre-defined methods (do not need to change) """

@app.before_request
def create_session():
    g.session = scoped_session(DBSession)

@app.teardown_appcontext
def shutdown_session(response_or_exc):
    sys.stdout.flush()
    g.session.commit()
    g.session.remove()

def connect_to_blockchains():
    try:
        # If g.acl has not been defined yet, then trying to query it fails
        acl_flag = False
        g.acl
    except AttributeError as ae:
        acl_flag = True
    
    try:
        if acl_flag or not g.acl.status():
            # Define Algorand client for the application
            g.acl = connect_to_algo()
    except Exception as e:
        print("Trying to connect to algorand client again")
        print(traceback.format_exc())
        g.acl = connect_to_algo()
    
    try:
        icl_flag = False
        g.icl
    except AttributeError as ae:
        icl_flag = True
    
    try:
        if icl_flag or not g.icl.health():
            # Define the index client
            g.icl = connect_to_algo(connection_type='indexer')
    except Exception as e:
        print("Trying to connect to algorand indexer client again")
        print(traceback.format_exc())
        g.icl = connect_to_algo(connection_type='indexer')

        
    try:
        w3_flag = False
        g.w3
    except AttributeError as ae:
        w3_flag = True
    
    try:
        if w3_flag or not g.w3.isConnected():
            g.w3 = connect_to_eth()
    except Exception as e:
        print("Trying to connect to web3 again")
        print(traceback.format_exc())
        g.w3 = connect_to_eth()
        
""" End of pre-defined methods """
        
""" Helper Methods (skeleton code for you to implement) """
def check_sig(payload,sig):
    try:
        sender_pk = payload["sender_pk"]
        platform = payload['platform']
        if platform == 'Ethereum':
            encoded_payload = json.dumps(payload).encode('utf-8')
            new_payload = eth_account.messages.encode_defunct(primitive = encoded_payload)
            return True if eth_account.Account.recover_message(new_payload,signature = sig) == sender_pk else False
        if platform == 'Algorand':
            payload_string = json.dumps(payload)
            return True if algosdk.util.verify_bytes(payload_string.encode('utf-8'),sig,sender_pk) == True else False
        return False
    except Exception as e:
        import traceback
        print(traceback.format_exc())

def log_message(message_dict):
    msg = json.dumps(message_dict)

    # TODO: Add message to the Log table
    
    return

def get_algo_keys():
    
    # TODO: Generate or read (using the mnemonic secret) 
    # the algorand public/private keys
    algo_sk = "18ppT/MQyz7nvq4ipbIEAOqA5lKrv4M+J09iHKU9tsAgDtPesktIeJ/67fB2KDk9qyAEQ8Xu/IOsqB/xHOaTeg=="
    algo_pk = "EAHNHXVSJNEHRH725XYHMKBZHWVSABCDYXXPZA5MVAP7CHHGSN5GXM2VWM"
    
    return algo_sk, algo_pk


def get_eth_keys(filename = "eth_mnemonic.txt"):
    # w3 = Web3()
    eth_pk = "0x1BcA01B4E665FE11804b89A6e91d857D354aeC1F"  #eth address
    eth_sk = b'\xad\\\xcb\x84-\xc2\xbf\xc0\xb1d\xf5\x82\x8e\x18kT\x906#\xd5\xbc\xdf|[\xeeK\xad\xc1\xf4\x98\xf5\xd6' #secret key

    # TODO: Generate or read (using the mnemonic secret) 
    # the ethereum public/private keys

    return eth_sk, eth_pk
def calc_new_sell_amount(curr_order, other_order):
    ratio = curr_order.sell_amount / curr_order.buy_amount
    print(ratio)
    return (curr_order.buy_amount - other_order.sell_amount) * ratio
    
# def process_child(order):
#     matches =  g.session.query(Order).filter(Order.buy_currency == order.sell_currency,
#                             Order.sell_currency == order.buy_currency,
#                             Order.filled == None,
#                             (Order.sell_amount / Order.buy_amount) >= (order.buy_amount / order.sell_amount))
#     g.session.add(order)
#     if not matches.first():
#         g.session.commit()
#         return
#     first_match = matches.first()
#     timestamp = datetime.now()
#     order.filled = timestamp
#     first_match.filled = timestamp
#     g.session.commit()
#     first_match.counterparty_id = order.id
#     order.counterparty_id = first_match.id
#     g.session.commit()
#     if order.buy_amount > first_match.sell_amount:
#         child_order = Order(creator_id=order.id,sender_pk=order.sender_pk,
#                     receiver_pk=order.receiver_pk, buy_currency=order.buy_currency, 
#                     sell_currency=order.sell_currency, buy_amount=order.buy_amount - first_match.sell_amount, 
#                     sell_amount=calc_new_sell_amount(order, first_match))     
#         process_child(order)

#     elif first_match.buy_amount > order.sell_amount:
#         child_order = Order(creator_id=first_match.id,sender_pk=first_match.sender_pk,
#         receiver_pk=first_match.receiver_pk, buy_currency=first_match.buy_currency, 
#         sell_currency=first_match.sell_currency, 
#         buy_amount=first_match.buy_amount - order.sell_amount, 
#         sell_amount=calc_new_sell_amount(first_match, order)) 
#         process_child(child_order)
  
def fill_order(order,txes):
    
    # order = Order(sender_pk=order['sender_pk'],receiver_pk=order['receiver_pk'], 
    #                 buy_currency=order['buy_currency'], sell_currency=order['sell_currency'], 
    #                 buy_amount=order['buy_amount'], sell_amount=order['sell_amount'])
    g.session.add(order)
    g.session.commit()
    matching_orders = g.session.query(Order).filter(Order.buy_currency == order.sell_currency,
                      Order.sell_currency == order.buy_currency,
                      Order.filled == None,
                     (Order.sell_amount / Order.buy_amount) >= (order.buy_amount / order.sell_amount))

    # No matching orders found, so insert new order and terminate
    if not matching_orders.first():
        return

    # get first match
    
    first_match = matching_orders.first()
    timestamp = datetime.now()
    order.filled = timestamp
    first_match.filled = timestamp
    #commit to set ID 
    g.session.commit()
    order.counterparty_id = first_match.id
    first_match.counterparty_id = order.id
    g.session.commit()
    # print(session.query(Order).all())

    #FIXME: create execute order here 
    # parameters = ["order_id", "platform", "receiver_pk", "amount"]
    # first_match_tx = dict(zip(parameters, create_txes(first_match)))
    # order_tx = dict(zip(parameters,create_txes(order)))
    first_match_tx = create_txes(first_match)
    order_tx = create_txes(order)
    txes.append(first_match_tx)
    txes.append(order_tx)


    if order.buy_amount > first_match.sell_amount:
        child_order = Order(creator_id=order.id,sender_pk=order.sender_pk,
                    receiver_pk=order.receiver_pk, buy_currency=order.buy_currency, 
                    sell_currency=order.sell_currency, buy_amount=order.buy_amount - first_match.sell_amount, 
                    sell_amount=calc_new_sell_amount(order, first_match)) 
        fill_order(child_order,txes)

    elif first_match.buy_amount > order.sell_amount:
        child_order = Order(creator_id=first_match.id,sender_pk=first_match.sender_pk,
                        receiver_pk=first_match.receiver_pk, buy_currency=first_match.buy_currency, 
                        sell_currency=first_match.sell_currency, 
                        buy_amount=first_match.buy_amount - order.sell_amount, 
                        sell_amount=calc_new_sell_amount(first_match, order)) 
        fill_order(child_order,txes)
    return txes
def create_txes(order):
    parameters = ["order_id", "platform", "receiver_pk", "amount"]
    #FIXME: platform might have to be buy_currency
    matches = [order.id, order.buy_currency, order.receiver_pk, order.sell_amount]
    return dict(zip(parameters,matches))
    # return [order.id, order.sell_currency, order.receiver_pk, order.sell_amount]
def execute_txes(txes):
    
    if txes is None:
        return True
    if len(txes) == 0:
        return True
    print( f"Trying to execute {len(txes)} transactions" )
    print( f"IDs = {[tx['order_id'] for tx in txes]}" )
    eth_sk, eth_pk = get_eth_keys()
    algo_sk, algo_pk = get_algo_keys()
    
    if not all( tx['platform'] in ["Algorand","Ethereum"] for tx in txes ):
        print( "Error: execute_txes got an invalid platform!" )
        print( tx['platform'] for tx in txes )

    algo_txes = [tx for tx in txes if tx['platform'] == "Algorand" ]
    eth_txes = [tx for tx in txes if tx['platform'] == "Ethereum" ]

    # TODO: 
    #       1. Send tokens on the Algorand and eth testnets, appropriately
    #          We've provided the send_tokens_algo and send_tokens_eth skeleton methods in send_tokens.py
    #       2. Add all transactions to the TX table
    acl = connect_to_algo("algodclient")
    algo_txes = send_tokens_algo(acl, algo_sk, algo_txes)
    
    w3 = connect_to_eth()
    eth_txes = send_tokens_eth(w3,eth_sk,eth_txes)

    add_to_tx_table(algo_txes)
    add_to_tx_table(eth_txes)

    pass

def add_to_tx_table(txes):
    for tx in txes:
        new_tx_obj = TX(
            platform = tx['platform'],
            receiver_pk = tx['receiver_pk'],
            order_id = tx['order_id'],
            tx_id = tx['tx_id']
        )
        g.session.add(new_tx_obj)
        g.session.commit()

""" End of Helper methods"""
  
@app.route('/address', methods=['POST'])
def address():
    if request.method == "POST":
        content = request.get_json(silent=True)
        if 'platform' not in content.keys():
            print( f"Error: no platform provided" )
            return jsonify( "Error: no platform provided" )
        if not content['platform'] in ["Ethereum", "Algorand"]:
            print( f"Error: {content['platform']} is an invalid platform" )
            return jsonify( f"Error: invalid platform provided: {content['platform']}"  )
        
        if content['platform'] == "Ethereum":
            #Your code here
            eth_pk = "0x1BcA01B4E665FE11804b89A6e91d857D354aeC1F"
            return jsonify( eth_pk )
        if content['platform'] == "Algorand":
            #Your code here
            algo_pk = "EAHNHXVSJNEHRH725XYHMKBZHWVSABCDYXXPZA5MVAP7CHHGSN5GXM2VWM"
            return jsonify( algo_pk )

@app.route('/trade', methods=['POST'])
def trade():
    print( "In trade", file=sys.stderr )
    connect_to_blockchains()
    # get_keys()
    if request.method == "POST":
        content = request.get_json(silent=True)
        columns = [ "buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform", "tx_id", "receiver_pk"]
        fields = [ "sig", "payload" ]
        error = False
        for field in fields:
            if not field in content.keys():
                print( f"{field} not received by Trade" )
                error = True
        if error:
            print( json.dumps(content) )
            return jsonify( False )
        
        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print( f"{column} not received by Trade" )
                error = True
        if error:
            print( json.dumps(content) )
            return jsonify( False )
        
        # Your code here
        if not check_sig(content['payload'], content['sig']):
            log_obj = Log(
                message = json.dumps(content['payload'])
            )
            g.session.add(log_obj)
            g.session.commit()
        
        # 1. Check the signature
        
        # 2. Add the order to the table
        
        order_obj = Order(
             sender_pk = content["payload"]["sender_pk"],
             receiver_pk = content["payload"]["receiver_pk"],
             buy_currency = content["payload"]["buy_currency"],
             sell_currency = content["payload"]["sell_currency"],
             buy_amount = content["payload"]["buy_amount"],
             sell_amount = content["payload"]["sell_amount"],
             tx_id = content['payload']['tx_id']
        )
        #FIXME: dunno if i actually implement this part
        # 3a. Check if the order is backed by a transaction equal to the sell_amount (this is new)

        # if order_obj.sell_currency  == "Ethereum":
        #     tx = w3.eth.get_transaction(order_obj.tx_id)
        #     if tx['to'] != get_eth_keys[1]:
        #         return jsonify(False)
        g.session.add(order_obj)
        g.session.commit()
        txes = []
        # 3b. Fill the order (as in Exchange Server II) if the order is valid
        final_txes = fill_order(order_obj,txes)
        # 4. Execute the transactions
        execute_txes(final_txes)
        # If all goes well, return jsonify(True). else return jsonify(False)
        return jsonify(True)

@app.route('/order_book')

def order_book():
    """
    FIXME:
    return list of all orders in database. FORMAT as JSON
    must contain tx_id of payment sent by MY server

    """
    fields = [ "buy_currency", "sell_currency", "buy_amount", "sell_amount", "signature", "tx_id", "receiver_pk", "sender_pk" ]
    data = {}
    result = []
    returned_orders = g.session.query(Order).all()
    for order in returned_orders:
        row = {
            "sender_pk": order.sender_pk,
            "receiver_pk": order.receiver_pk,
            "buy_currency": order.buy_currency,
            "sell_currency": order.sell_currency,
            "buy_amount": order.buy_amount,
            "sell_amount": order.sell_amount,
            "signature": order.signature,
            "tx_id": order.tx_id
        }
        result.append(row)
    data["data"] = result

    return jsonify(data)

    # Same as before
    pass

if __name__ == '__main__':
    app.run(port='5002')

