from duniterpy.key import SigningKey
from silkaj.tools import message_exit


async def patched_transaction_confirmation(
    issuer_pubkey,
    pubkey_amount,
    tx_amounts,
    outputAddresses,
    outputBackChange,
    comment,
):
    if not (
        (
            isinstance(issuer_pubkey, str)
            and isinstance(pubkey_amount, int)
            and isinstance(tx_amounts, list)
            and isinstance(outputAddresses, list)
            and isinstance(comment, str)
            and isinstance(outputBackchange, str)
        )
        and len(tx_amounts) == len(outputAddresses)
        and sum(tx_amounts) <= pubkey_amount
    ):
        message_exit(
            "Test error : patched_transaction_confirmation() : Parameters are not coherent"
        )


async def patched_handle_intermediaries_transactions(
    key,
    issuers,
    tx_amounts,
    outputAddresses,
    Comment="",
    OutputbackChange=None,
):
    if not (
        (
            isinstance(key, SigningKey)
            and isinstance(issuers, str)
            and isinstance(tx_amounts, list)
            and isinstance(outputAddresses, list)
            and isinstance(Comment, str)
            and (isinstance(OutputBackchange, str) or OutputbackChange == None)
        )
        and len(tx_amounts) == len(outputAddresses)
        and key.pubkey() == issuers
    ):
        message_exit(
            "Test error : patched_handle_intermediaries_transactions() : Parameters are not coherent"
        )


async def patched_generate_and_send_transaction(
    key,
    issuers,
    tx_amounts,
    listinput_and_amount,
    outputAddresses,
    Comment,
    OutputbackChange,
):
    if not (
        (
            isinstance(key, SigningKey)
            and isinstance(issuers, str)
            and isinstance(tx_amounts, list)
            and isinstance(listinput_and_amount, tuple)
            and isinstance(outputAddresses, list)
            and isinstance(Comment, str)
            and isinstance(OutputBackchange, str)
        )
        and len(tx_amounts) == len(outputAddresses)
        and sum(tx_amounts) <= listinput_and_amount[2]
        and key.pubkey() == issuers
    ):
        message_exit(
            "Test error : patched_generate_and_send_transaction() : Parameters are not coherent"
        )
    pass
