#!/usr/bin/python3
from gen_keys import addr
from algosdk.v2client import algod
from algosdk.v2client import indexer
from algosdk import account
from algosdk.future import transaction
from models import Base, Order, TX, Log

def connect_to_algo(connection_type=''):
    #Connect to Algorand node maintained by PureStake
    algod_token = "B3SU4KcVKi94Jap2VXkK83xx38bsv95K5UZm2lab"
    
    if connection_type == "indexer":
        # return an instance of the v2client indexer. This is used for checking payments for tx_id's
        algod_address = "https://testnet-algorand.api.purestake.io/idx2"
        # indexer_token = algod_token
        headers = {
            'X-API-Key': algod_token
        }
        return indexer.IndexerClient(algod_token,algod_address,headers)
    else:
        algod_address = "https://testnet-algorand.api.purestake.io/ps2"
        purestake_token = {
            'X-Api-key': algod_token
        }
        algodclient = algod.AlgodClient(algod_token, algod_address, headers=purestake_token)
        return algodclient

def send_tokens_algo( acl, sender_sk, txes):
    params = acl.suggested_params()
    sender_pk = account.address_from_private_key(sender_sk)
    for i,tx in enumerate(txes):
        params.first += 1
        send_amount = int(tx['amount'])
        send_to_address = tx['receiver_pk']
        signed_tx = None
        try:
            unsigned_tx = transaction.PaymentTxn(sender_pk, params, send_to_address, send_amount)
            signed_tx = unsigned_tx.sign(sender_sk)

            print(f"Sending {tx['amount']} microalgo from {sender_pk} to {tx['receiver_pk']}")
            # Send the transaction to the testnet
            acl.send_transaction(signed_tx)
            tx_id = signed_tx.transaction.get_txid()
            txinfo = wait_for_confirmation_algo(acl, txid=tx_id )
            print("txinfo here:")
            print(txinfo)
            print(f"Sent {tx['amount']} microalgo in transaction: {tx_id}\n")
            tx['tx_id'] = tx_id

            checking_id = tx['order_id']
            print(f"CURRENTLY IN SEND ALGO. the ORDER_ID is: {checking_id}")
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            print(e)
    return txes

# Function from Algorand Inc.
def wait_for_confirmation_algo(client, txid):
    """
    Utility function to wait until the transaction is
    confirmed before proceeding.
    """
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print("Transaction {} confirmed in round {}.".format(txid, txinfo.get('confirmed-round')))
    return txinfo

##################################

from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import TransactionNotFound
import json
import progressbar


def connect_to_eth():
    IP_ADDR='3.23.118.2' #Private Ethereum
    PORT='8545'
    w3 = Web3(Web3.HTTPProvider('http://' + IP_ADDR + ':' + PORT))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0) #Required to work on a PoA chain (like our private network)
    w3.eth.account.enable_unaudited_hdwallet_features()
    
    if w3.isConnected():
        return w3
    else:
        print( "Failed to connect to Eth" )
        return None

def wait_for_confirmation_eth(w3, tx_hash):
    print( "Waiting for confirmation" )
    widgets = [progressbar.BouncingBar(marker=progressbar.RotatingMarker(), fill_left=False)]
    i = 0
    with progressbar.ProgressBar(widgets=widgets, term_width=1) as progress:
        while True:
            i += 1
            progress.update(i)
            try:
                receipt = w3.eth.get_transaction_receipt(tx_hash)
            except TransactionNotFound:
                continue
            break 
    return receipt

####################
def send_tokens_eth(w3,sender_sk,txes):
    sender_account = w3.eth.account.privateKeyToAccount(sender_sk)
    sender_pk = sender_account._address
    nonce = w3.eth.get_transaction_count(sender_pk,"pending")
    # For each of the txes, sign and send them to the testnet
    # Track the nonce -locally-
    for i,tx in enumerate(txes):
        receiver_pk = tx['receiver_pk']
        tx_amount = int(tx['amount'])
        txdict = {
            'nonce':nonce + i,
            'gasPrice': w3.eth.gas_price,
            'gas': w3.eth.estimate_gas({'from': sender_pk, 'to': receiver_pk,'data':b'','amount': tx_amount }),
            'to': receiver_pk,
            'value': tx_amount,
            'data': b''
        }
        signed_txn = w3.eth.account.sign_transaction(txdict,sender_sk)
        tx_id = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        receipt = wait_for_confirmation_eth(w3,tx_id)
        tx['tx_id'] = tx_id
        checkingid = tx['order_id']
    return txes