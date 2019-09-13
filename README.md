# ECRanner

![](https://github.com/homoluctus/ecranner/workflows/Lint%20and%20Test/badge.svg)

This is that scan the vulnerability of Docker images stored in ECR.<br>

## Feature
- Pull Docker Image From ECR
- Vulnerability Scan
  - [Trivy](https://github.com/aquasecurity/trivy) detects software (OS package and application library) vulnerabilities in Docker Image
- Slack Integration
  - Push vulnerability information to Slack. Slack UI is as following:

    <img src="https://github.com/homoluctus/ecranner/blob/master/slack_ui.png" alt="Slack-UI" width="70%">

## How to use
### 1. Create .env file
docker-compose.ymlと同階層に`.env`を作成し、以下の項目を設定してください

|Parameter|REQUIRED/OPTIONAL|DESCRIPTION|
|:--:|:--:|:--|
|AWS_ACCOUNT_ID|REQUIRED||
|AWS_ACCESS_KEY_ID|REQUIRED||
|AWS_SECRET_ACCESS_KEY|REQUIRED||
|AWS_DEFAULT_REGION|OPTIONAL|default: us-east-1|
|SLACK_WEBHOOK|REQUIRED|Slack Incoming Webhooks URL<br>reference: https://api.slack.com/incoming-webhooks|
|SLACK_CHANNEL|OPTIONAL|Slack channel that you want post message|
|SLACK_ICON|OPTIONAL|Specify icon_url or icon_emoji<br>default: `:trivy:`|
|IMAGE_TAG|OPTIONAL|Docker image tag<br>default: latest|
|TZ|OPTIONAL|timezone|
|LOG_LEVEL|OPTIONAL|default: INFO<br>servirity: DEBUG, INFO, WARNING, ERROR, CRITICAL<br>reference: [Logging HOWTO — Python 3.7.4 documentation](https://docs.python.org/3/howto/logging.html#when-to-use-logging)|


### 2. Pull image

```
docker pull iscream/ecranner
```

### 3. Execute docker container

```
docker run --env-file ./.env --privileged iscream/ecranner
```