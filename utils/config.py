from dotenv import load_dotenv
import os


load_dotenv()

MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2mb
ACCESS_TOKEN_EXPIRE_MINUTES = 8 * 60  # 8 hours
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
CACHE_EXPIRED = 86400  # 1 day
ALGORITHM = "HS256"

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
JWT_REFRESH_SECRET_KEY = os.environ.get('JWT_REFRESH_SECRET_KEY')

BACKEND_URL = os.environ.get('BACKEND_URL')
BACKEND_PORT = os.environ.get('BACKEND_PORT')
LINK_FRONTEND = os.environ.get('LINK_FRONTEND')

DB_HOSTNAME = os.environ.get('DB_HOSTNAME')
DB_PORT = os.environ.get('DB_PORT')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

REDIS_URL = os.environ.get('REDIS_URL')
ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')
KAFKA_CONNECT_URL = os.environ.get('KAFKA_CONNECT_URL')

# print(JWT_SECRET_KEY)
# print(JWT_REFRESH_SECRET_KEY)

# print(BACKEND_URL)
# print(BACKEND_PORT)
# print(LINK_FRONTEND)

# print(DB_HOSTNAME)
# print(DB_PORT)
# print(DB_USER)
# print(DB_PASSWORD)
# print(DB_NAME)

# print(REDIS_URL)
# print(ELASTICSEARCH_URL)
# print(KAFKA_CONNECT_URL)
