
import os
from covid import DailyData
from make_charts import run_make_charts
from make_table import run_make_table
import sys

def main(creds):
    DailyData(creds)
    run_make_charts(creds)
    run_make_table(creds)
    return {
        'statusCode': 200,
        'body': 'covid job run successfully'
    }

# main({
#     'aws_access_key_id': os.environ['aws_access_key_id'],
#     'aws_secret_access_key': os.environ['aws_secret_access_key'],
#     'env': 'dev'
# })