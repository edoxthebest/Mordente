import logging

logger = logging.getLogger('SELinuxTool')
logFormatter = logging.Formatter('%(asctime)s [%(levelname)-5.5s]  %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(logFormatter)
logger.addHandler(handler)

rlogger = logging.getLogger('SELinuxTool:r')
rhandler = logging.StreamHandler()
rhandler.terminator = '\r'
rhandler.setFormatter(logFormatter)
rlogger.addHandler(rhandler)

flogger = logging.getLogger('SELinuxTool:f')
flogFormatter = logging.Formatter('[%(levelname)-5.5s]  %(message)s')
file_handler = logging.FileHandler('log/default.log')
file_handler.setFormatter(flogFormatter)
flogger.addHandler(file_handler)

blogger = logging.getLogger('SELinuxTool:b')
blogger.addHandler(handler)
blogger.addHandler(file_handler)
