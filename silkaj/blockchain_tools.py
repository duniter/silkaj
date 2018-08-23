from silkaj.network_tools import get_request


class BlockchainParams(object):
    __instance = None

    def __new__(cls, ep):
        if BlockchainParams.__instance is None:
            BlockchainParams.__instance = object.__new__(cls)
        return BlockchainParams.__instance

    def __init__(self, ep):
        self.params = get_request(ep, "blockchain/parameters")
