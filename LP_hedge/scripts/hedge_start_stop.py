import subprocess


def start_hedge_process(cid):
    process = subprocess.Popen(['python', 'scripts/hedge_process.py', cid], shell=True)


def stop_hedge_process(cid):
    pass
    # delete_process_from_db(cid)



# api_key = sys.argv[1]
# api_secret = sys.argv[2]
# subaccount_name = sys.argv[3]
# cid = int(sys.argv[4])

# data = {'cid': 1440189840, 'status': 'active',
#         'api': {'api-key': 'mu9Zuxq9xJyUsKrqhk2igqYChvFgjTDA2hZ-G9O8', 'api-secret': 'VmIcl_MGiVqlLFsqJFoHDtQBvQq5AOoqGvi2PTx6',
#                 'sub-account': 'bot_test'}}
#
# api_key = data['api']['api-key']
# api_secret = data['api']['api-secret']
# subaccount_name = data['api']['sub-account']
# cid = str(data['cid'])
#
#
#
#
#
# format_log = "%(asctime)s: %(message)s"
# logging.basicConfig(format=format_log, level=logging.INFO, filename=f"log {cid}.txt",
#                     datefmt="%H:%M:%S")
#
#
# i = 0
# time.sleep(1)
#
# # while True:
# while i < 60:
#     print(i)
#     bot.check_positions()
#     print('short_positions ', bot.short_positions)
#     print('pools_positions ', bot.pools_positions)
#     logging.info('short_positions ', bot.short_positions)
#     logging.info('pools_positions ', bot.pools_positions)
#     time.sleep(60)
#     i += 1
