import logging
import config

logging.basicConfig(
  level=logging.DEBUG,
  format='%(asctime)s - %(levelname)s - %(message)s',
  filename=config.LOG_PATH,
  filemode='a'
)