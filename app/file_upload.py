"""Utility in order to upload files to S3 object storage."""
import boto3
import argparse


class CommandLine:
    def __init__(self) -> None:
        parser = argparse.ArgumentParser(description='Parser description')
        parser.add_argument(
            '-r',
            '--region',
            help = 'Provide region of the object storage.',
            required = True,
        )
        parser.add_argument(
            '-u',
            '--endpointUrl',
            help = 'Provide endpoint url of the object storage.',
            required = True,
        )
        parser.add_argument(
            '-ac',
            '--awsAccessKeyId',
            help = 'Provive aws access key id.',
            required = True,
        )
        parser.add_argument(
            '-sc',
            '--awsSecretAccessKey',
            help = 'Provive aws secret access key.',
            required = True,
        )
        parser.add_argument(
            '-b',
            '--bucket',
            help = 'Provive bucket name to be created.',
            required = True,
        )
        parser.add_argument(
            '-k',
            '--key',
            help = 'Provive key to write the file to.',
            required = True,
        )
        parser.add_argument(
            '-i',
            '--input',
            help = 'Provive the file name to load.',
            required = True,
        )
        argument = parser.parse_args()
        s3_client = boto3.client(
            's3',
            region_name=argument.region,
            endpoint_url=argument.endpointUrl,
            aws_access_key_id=argument.awsAccessKeyId,
            aws_secret_access_key=argument.awsSecretAccessKey,
        )
        buckets = s3_client.list_buckets().get('Buckets', list())
        creationNeeded = True
        for bucket in buckets:
            if bucket['Name'] == argument.bucket:
                creationNeeded = False
        if creationNeeded:
            print('[INFO] Bucket non existent, need to create. Creating...')
            s3_client.create_bucket(Bucket=argument.bucket)
        print('[INFO] Uploading file...')
        s3_client.upload_file(argument.input, argument.bucket, argument.key)

if __name__ == '__main__':
    app = CommandLine()
