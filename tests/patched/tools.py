from silkaj.constants import G1_SYMBOL


# mock CurrencySymbol().symbol
async def patched_currency_symbol(self):
    return G1_SYMBOL
