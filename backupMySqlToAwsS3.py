#!/usr/bin/env python3

### Author: sDK
### Date: 16-Nov-24 18:21
### License : MIT
### Works and Tested with Cron.

import os
import boto3
import logging
from datetime import datetime
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, BotoCoreError

logging.basicConfig(filename='crmDbBackup.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')
                    
# IAM Role needs to be provisioned for the script to run on EC2 instance. (IAM Role - Auto-Rotates)
# TODO: Follow BstPrctce. Store & Pull DB Creds from AWS Secrets Manager. Helpful in auto rotation of secrets.
DB_CONFIG_PATH = os.getenv('MYSQL_CONFIG_PATH') # For now, get database creds from env => ~/.my.cnf
S3_BUCKET_NAME = 'crm-db-backup'
DB_NAME = os.getenv('DB_NAME')

def backup_database():
    backup_file = f"{DB_NAME}_{datetime.now().strftime('%Y%m%d%H%M%S')}.sql"
    
    # mysql has variants to mysqldump command
    dump_command = f"mysqldump --defaults-file={DB_CONFIG_PATH} {DB_NAME} > {backup_file}" 
    dump_status = os.system(dump_command)
    if dump_status != 0:
        logging.error("mysqldump FAILed")
        return None
    logging.info(f"Backup OKAY: {backup_file}")
    return backup_file

def upload_to_s3(file_name):
    s3 = boto3.client('s3')
    try:
        s3.upload_file(file_name, S3_BUCKET_NAME, file_name)
        logging.info(f"Upload OKAY: {file_name}")
    except (NoCredentialsError, PartialCredentialsError, BotoCoreError) as e:
        logging.error(f"Upload ERROR: {e}")
        return False
    return True
    
if __name__ == "__main__":
    backup_file = backup_database()
    if backup_file:
        if upload_to_s3(backup_file):
            os.remove(backup_file)
            logging.info(f"Backup file deleted from ec2 after s3 upload: {backup_file}")
        else:
            logging.error("Backup file NOT deleted due to upload failure.")
    else:
        logging.error("Backup FAILed. Nothing uploaded.")
