# !/usr/bin/python
import time

from eth_account import Account
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.types import TxParams

from flatlaunchpeg import FLATLAUNCHPEG_ABI


# See the README.md for more information.

def main():
    print('Loading')

    # Settings for the mint. I've put in examples so you know what should go in here.
    # Make sure you replace the contract address and private key!
    # What NFT are you minting?
    contract_address = '0x048c939bEa33c5dF4d2C69414B9385d55b3bA62E'
    # Your private key; use a special-purpose low asset account.
    private_key = '0xf964f5e1d7acf7265dfec7cd70821324786a2271e4bddf6a3d3630e45ee1015c'
    # This should be enough gas, but you might have to boost it if you're minting a lot of NFTs at one time.
    gas_limit = 300_000
    # This is the 'max' gas; you will only actually pay whatever the block fee ends up being.
    max_gas_in_gwei = 50
    # This is a tip; higher tips get placed earlier in the block.
    gas_tip_in_gwei = 2

    # Load the account, connect to Avalanche, and prepare the mint contract proxy.
    account = Account.from_key(private_key)
    node_uri = 'https://api.avax.network/ext/bc/C/rpc'
    w3 = Web3(Web3.HTTPProvider(node_uri))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    mint_contract = w3.eth.contract(address=Web3.toChecksumAddress(contract_address), abi=FLATLAUNCHPEG_ABI)

    # Load some stuff from the contract. You could hardcode these values instead.
    start_time = mint_contract.functions.publicSaleStartTime().call()
    price = mint_contract.functions.salePrice().call()
    quantity = mint_contract.functions.maxPerAddressDuringMint().call()
    print('Detected Configuration:')
    print('  start_time:', start_time)
    print('  price:', price)
    print('  quantity:', quantity)
    print('Cur time:', int(time.time()))

    # Loop until the mint is ready.
    while time.time() - start_time < 0:
        time.sleep(.1)

    # Create the basic transaction that we're going to send.
    base_tx: TxParams = {
        'type': 0x2,
        'chainId': w3.eth.chain_id,
        'gas': gas_limit,
        'maxFeePerGas': Web3.toWei(max_gas_in_gwei, 'gwei'),
        'maxPriorityFeePerGas': Web3.toWei(gas_tip_in_gwei, 'gwei'),
        'nonce': w3.eth.get_transaction_count(account.address),
        'value': price * quantity,
    }

    # Create the appropriate 'data' field and append it to the tx.
    contract_function = mint_contract.functions.publicSaleMint(quantity)
    contract_tx = contract_function.buildTransaction(base_tx)

    # Sign it, and send it.
    signed_tx = w3.eth.account.sign_transaction(contract_tx, account.privateKey)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # Wait for the tx to be included into the blockchain.
    hex_hash = w3.toHex(tx_hash)
    receipt = w3.eth.wait_for_transaction_receipt(hex_hash)

    # Dump the finalized tx to the console.
    print('Done!')
    print(receipt)


if __name__ == '__main__':
    main()
