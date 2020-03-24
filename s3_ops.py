
from ipdb import set_trace as b
import boto3
import pandas as pd
import s3fs
import os
import shutil

def write_html_to_s3(local_file, object_key, creds):
    if creds.get('env') == 'dev':
        dev_file_loc = local_file.replace('/tmp/', './dev_html/')
        shutil.copyfile(local_file, dev_file_loc)
        print('{} written to file'.format(dev_file_loc))
    else:
        client = boto3.client('s3', aws_access_key_id=creds['aws_access_key_id'], aws_secret_access_key=creds['aws_secret_access_key'])
        with open(local_file, 'rb') as body:
            response = client.put_object(ACL='public-read',Body=body,Key=object_key, Bucket="graycannon.com",ContentType='text/html')
        print('{} object written to s3'.format(object_key))

def write_csv_to_s3(df, filename, creds):
    if creds.get('env') == 'dev':
        dev_file_loc = './dev_csv/' + filename
        df.to_csv(dev_file_loc, index=None)
        print('{} written to file'.format(dev_file_loc))
    else:
        fs = s3fs.S3FileSystem(key=creds['aws_access_key_id'], secret=creds['aws_secret_access_key'])
        bytes_to_write = df.to_csv(None, index=None).encode()
        with fs.open('s3://graycannon.com/csvs/{}'.format(filename), 'wb') as f:
            f.write(bytes_to_write)
        print('csv/{} object wrtten to s3'.format(filename))

