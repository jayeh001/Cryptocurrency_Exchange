#!/usr/bin/python3
from gen_keys import addr
from algosdk.v2client import algod
from algosdk.v2client import indexer
from algosdk import account
from algosdk.future import transaction

def connect_to_algo(connection_type=''):
    #Connect to Algorand node maintained by PureStake
    algod_token = "B3SU4KcVKi94Jap2VXkK83xx38bsv95K5UZm2lab"
    
    if connection_type == "indexer":
        # return an instance of the v2client indexer. This is used for checking payments for tx_id's

        algod_address = "https://testnet-algorand.api.purestake.io/idx2"
        indexer_token = ""
        #FIXME: what is API key
        headers = {
            'X-API-Key': 'My API key'
        }
        return indexer.IndexerClient(indexer_token,algod_address,headers)

    else:
        # TODO: return an instance of the client for sending transactions
        # Tutorial Link: https://developer.algorand.org/tutorials/creating-python-transaction-purestake-api/
        algod_address = "https://testnet-algorand.api.purestake.io/ps2"
        purestake_token = {
            'X-Api-key': algod_token
        }
        algodclient = algod.AlgodClient(algod_token, algod_address, headers=purestake_token)
        return algodclient

def send_tokens_algo( acl, sender_sk, txes):
    params = acl.suggested_params
    
    # TODO: You might want to adjust the first/last valid rounds in the suggested_params
    #       See guide for details
    gh = params.gh
    first_valid_round = params.first
    last_valid_round = params.last
    fee = params.min_fee
    
    # TODO: For each transaction, do the following:
    #       - Create the Payment transaction 
    #       - Sign the transaction
    
    # TODO: Return a list of transaction id's

    sender_pk = account.address_from_private_key(sender_sk)
    send_to_address = addr #algo address 
    tx_ids = []
    for i,tx in enumerate(txes):
        send_amount = tx['amount']
        unsigned_tx = transaction.PaymentTxn(sender_pk, fee, first_valid_round, last_valid_round, gh, send_to_address, send_amount, flat_fee=True)

        signed_tx = unsigned_tx.sign(sender_sk)

        try:
            print(f"Sending {tx['amount']} microalgo from {sender_pk} to {tx['receiver_pk']}" )
            
            # TODO: Send the transaction to the testnet
            acl.send_transaction(signed_tx)
            tx_id = signed_tx.transaction.get_tx_id()
            tx_ids.append(tx_id)
            txinfo = wait_for_confirmation_algo(acl, txid=tx_id )
            print(f"Sent {tx['amount']} microalgo in transaction: {tx_id}\n" )
        except Exception as e:
            print(e)

    # return []
    return tx_ids

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
    # acct,mnemonic_secret = w3.eth.account.create_with_mnemonic()
    # acct = w3.eth.account.from_mnemonic(mnemonic_secret)
    # eth_pk = acct._address
    # eth_sk = acct._private_key
    # print(f"acct is: {acct}")
    # print(f"the addres is {acct._address}")
    # print(f"eth_pk is : {eth_pk}")
    # print(f"eth_sk is : {eth_sk}")
    # eth_pk = "0x1BcA01B4E665FE11804b89A6e91d857D354aeC1F"  #eth address
    # eth_sk = b'\xad\\\xcb\x84-\xc2\xbf\xc0\xb1d\xf5\x82\x8e\x18kT\x906#\xd5\xbc\xdf|[\xeeK\xad\xc1\xf4\x98\xf5\xd6' #secret key
    if w3.isConnected():
        return w3
    else:
        print( "Failed to connect to Eth" )
        return None

# connect_to_eth()

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

    # TODO: For each of the txes, sign and send them to the testnet
    # Make sure you track the nonce -locally-
    
    tx_ids = []
    for i,tx in enumerate(txes):
        # Your code here
        continue

    return tx_ids
