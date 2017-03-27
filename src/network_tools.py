from __future__ import unicode_literals
import ipaddress
import json
import socket
import urllib.request

def discover_peers(ep, discover):
    """
    From first node, discover his known nodes.
    Remove from know nodes if nodes are down.
    If discover option: scan all network to know all nodes.
        display percentage discovering.
    """
    endpoints = parse_endpoints(request(ep, "network/peers")["peers"])
    if discover: print("Discovering network")
    for i, ep in enumerate(endpoints):
        if discover: print("{0:.0f}%".format(i/len(endpoints) * 100)) #, ep) # debug
        if best_node(ep, 0) is None: endpoints.remove(ep)
        elif discover: endpoints = recursive_discovering(endpoints, ep)
    return endpoints

def recursive_discovering(endpoints, ep):
    """
    Discover recursively new nodes.
    If new node found add it and try to found new node from his known nodes.
    """
    news = parse_endpoints(request(ep, "network/peers")["peers"])
    for new in news:
#        print("-", new) # debug
        if best_node(new, 0) is not None and new not in endpoints:
            endpoints.append(new)
            recursive_discovering(endpoints, new)
    return endpoints
    # Check why network discovering stayed stuck when checking some node without domain name: it happen sometimes

def parse_endpoints(rep):
    """
    endpoints[]{"domain", "ip4", "ip6", "pubkey"}
    list of dictionaries
    reps: raw endpoints
    """
    i, j, endpoints = 0, 0, []
    while (i < len(rep)):
        if (rep[i]["status"] == "UP"):
            while j < len(rep[i]["endpoints"]):
                ep = parse_endpoint(rep[i]["endpoints"][j])
                j+=1
                if ep is None:
                    break
                ep["pubkey"] = rep[i]["pubkey"]
                endpoints.append(ep)
        i+=1; j = 0
    return endpoints

def parse_endpoint(rep):
    """
    rep: raw endpoint, sep: split endpoint
    domain, ip4 or ip6 could miss on raw endpoint
    """
    ep, sep = {}, rep.split(" ")
    if sep[0] == "BASIC_MERKLED_API":
        if check_port(sep[-1]): ep["port"] = sep[-1]
        if len(sep) == 5 and check_ip(sep[1]) == 0 and check_ip(sep[2]) == 4 and check_ip(sep[3]) == 6:
            ep["domain"], ep["ip4"], ep["ip6"] = sep[1], sep[2], sep[3]
        if len(sep) == 4:
            ep = endpoint_type(sep[1], ep)
            ep = endpoint_type(sep[2], ep)
        if len(sep) == 3:
            ep = endpoint_type(sep[1], ep)
        return ep
    else:
        return None

def endpoint_type(sep, ep):
    typ = check_ip(sep)
    if typ == 0: ep["domain"] = sep
    if typ == 4: ep["ip4"] = sep
    if typ == 6: ep["ip6"] = sep
    return ep

def check_ip(address):
    try: return ipaddress.ip_address(address).version
    except: return 0

def request(ep, path):
    address = best_node(ep, 0)
    if address is None: return address
    url = "http://" + ep[address] + ":" + ep["port"] + "/" + path
    if ep["port"] == "443":
        url = "https://" + ep[address] + "/" + path
    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request)
    encoding = response.info().get_content_charset('utf8')
    return json.loads(response.read().decode(encoding))

def post_request(ep, path, postdata):
    address = best_node(ep, 0)
    if address is None: return address
    url = "http://" + ep[address] + ":" + ep["port"] + "/" + path
    if ep["port"] == "443":
        url = "https://" + ep[address] + "/" + path
    request = urllib.request.Request(url,bytes(postdata, 'utf-8'))
    try:
        response = urllib.request.urlopen(request)
    except urllib.error.URLError as e:
        print(e)
        exit()
    encoding = response.info().get_content_charset('utf8')
    return json.loads(response.read().decode(encoding))

def best_node(ep, main):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addresses, port = {"ip6", "ip4", "domain"}, int(ep["port"])
    for address in addresses:
        if address in ep:
            try:
                s.connect((ep[address], port))
                s.close()
                return address
            except: pass
    if main: print("Wrong node gived as argument"); exit()
    return None
    
def check_port(port):
    try:
        port = int(port)
    except:
        print("Port must be an integer"); exit()
    if (port < 0 or port > 65536):
        print("Wrong port number"); exit()
    return 1
