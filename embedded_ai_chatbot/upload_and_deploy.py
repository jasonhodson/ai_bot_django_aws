import subprocess
import os
import shutil
from datetime import datetime

current_datetime = datetime.now()
formatted_datetime = current_datetime.strftime('%Y%m%d%H%M%S')

elasticbeanstalk_application = "EmbededAIChatBot"
elasticbeanstalk_environment = "EmbededAIChatBot-env"
s3Bucket = "elasticbeanstalk-us-east-2-624562008531"
elasticbeanstalk_version = "embedded_ai_chatbot_" + formatted_datetime

def run_command(command, suppress_output=False):
    try:
        if suppress_output:
            with open(os.devnull, 'w') as devnull:
                process = subprocess.run(command, shell=True, check=True, stdout=devnull, stderr=devnull)
        else:
            process = subprocess.run(command, shell=True, check=True)
        print(f"Command succeeded: {command}")
        return process
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")
        exit(1)  # Stop the script execution

def main():
    # Zip the file for deployment
    run_command(f'zip -r {elasticbeanstalk_version}.zip . -x "*.pyc" -x "__pycache__/*" -x "*.DS_Store" -x "upload_and_deploy.py"')

    # Upload the zip file to AWS S3 Bucket
    run_command(f"aws s3 cp {elasticbeanstalk_version}.zip s3://{s3Bucket}/{elasticbeanstalk_version}.zip")

    # Create Elastic Beanstalk application version
    run_command(f'aws elasticbeanstalk create-application-version --application-name {elasticbeanstalk_application} --version-label {elasticbeanstalk_version} --source-bundle S3Bucket="{s3Bucket}",S3Key="{elasticbeanstalk_version}.zip"', suppress_output=True)

    # Update Elastic Beanstalk environment
    run_command(f"aws elasticbeanstalk update-environment --environment-name {elasticbeanstalk_environment} --version-label {elasticbeanstalk_version}", suppress_output=True)

    # Deletes the zip file after deployment
    run_command(f'rm {elasticbeanstalk_version}.zip')

if __name__ == "__main__":
    main()