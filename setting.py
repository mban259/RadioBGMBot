import json

def load_setting():
    global discord_token, radio_role, xpc_jp, radio_vc, helplist, admin
    with open('data/setting.json') as f:
        d = json.loads(f.read())
        xpc_jp = d['xpc_jp']
        radio_vc = d['radio_vc']
        radio_role = d['radio_role']
        discord_token = d['discord_token']
        admin = d['admin']

    with open('data/help/helplist.txt') as f:
        helplist = f.read()