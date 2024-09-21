import os

TEST = 'test'
PROD = 'production'
DEV = 'development'
ENVIRONMENT = os.getenv('ENVIRONMENT', TEST)

DATABASE_FILENAME = f"database_switcher.sqlite"