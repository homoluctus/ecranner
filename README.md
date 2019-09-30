# ECRanner

![](https://github.com/homoluctus/ecranner/workflows/Test/badge.svg)
![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/homoluctus/ecranner?include_prereleases)
![GitHub](https://img.shields.io/github/license/homoluctus/ecranner)

This is that scan the vulnerability of Docker images stored in ECR.<br>

# Table of contents
- [Feature](#feature)
- [Get Started](#get-started)
  - [Install Prerequirements](#install-prerequirements)
  - [Install ECRanner](#install-ecranner)
  - [Write ecranner.yml](#write-ecranner.yml)
  - [Execute](#execute)
- [Configuration Parameter](#configuration-parameter)
- [Command options](#command-options)

# Feature
- Pull Docker Image From ECR
- Support multi account
- Vulnerability Scan
  - [Trivy](https://github.com/aquasecurity/trivy) detects software (OS package and application library) vulnerabilities in Docker Image
- Slack Integration
  - Push vulnerability information to Slack. Slack UI is as following:

    <img src="https://raw.githubusercontent.com/homoluctus/ecranner/master/slack_ui.png" alt="Slack-UI" width="70%">

# Get Started
## Install Prerequirements

- [Trivy](https://github.com/aquasecurity/trivy)
- Git (Used with Trivy)

## Install ECRanner

```
pip install ecranner
```

## Write ecranner.yml

A `ecranner.yml` looks like this:

```
aws:
  stg:
    account_id: xxxxxxxxx
    region: us-east-1
    aws_access_key_id: xxxxxxxxx
    aws_secret_access_key: xxxxxxxxx
    images:
      - image:latest
      - image:1.0-dev
  prod:
    account_id: xxxxxxxxx
    region: us-east-1
    aws_access_key_id: xxxxxxxxx
    aws_secret_access_key: xxxxxxxxx
    images:
      - image:1.4
      - image:5.3

trivy:
  path: ~/user/.local/bin/trivy
  options: --severity CRITICAL -q
```

## Execute

```
ecranner
```

You execute the above and then output the scan result to the console as follows:

```
[ { 'Target': 'image_name:latest'
              '(alpine 3.10.1)',
    'Vulnerabilities': [ { 'Description': 'aa_read_header in '
                                          'libavformat/aadec.c in FFmpeg '
                                          'before 3.2.14 and 4.x before 4.1.4 '
                                          'does not check for sscanf failure '
                                          'and consequently allows use of '
                                          'uninitialized variables.',
                           'FixedVersion': '4.1.4-r0',
                           'InstalledVersion': '4.1.3-r1',
                           'PkgName': 'ffmpeg',
                           'References': [ 'https://git.ffmpeg.org/gitweb/ffmpeg.git/shortlog/n4.1.4',
                                           'https://github.com/FFmpeg/FFmpeg/commit/ed188f6dcdf0935c939ed813cf8745d50742014b',
                                           'https://github.com/FFmpeg/FFmpeg/compare/a97ea53...ba11e40',
                                           'https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2019-12730',
                                           'http://www.securityfocus.com/bid/109317',
                                           'https://git.ffmpeg.org/gitweb/ffmpeg.git/commit/9b4004c054964a49c7ba44583f4cee22486dd8f2'],
                           'Severity': 'HIGH',
                           'Title': '',
                           'VulnerabilityID': 'CVE-2019-12730'}
```

# Configuration Parameter
Specify to use parameter in `ecranner.yml`.

- [v1.0](conf/v1-0.md)

# Command options

|option|required|default|description|
|:--:|:--:|:--:|:--|
|-f, --file|false|`./ecranner.yml`|Filepath to configuration in YAML.<br>Specify this option if you change configuration filename.|
|--env-file|false|`./.env`|Specify .env file path.<br>Automatically load .env file if this file is found in current directory.|
|--slack|false|N/A|Send the scan result to Slack.<br>If you use this option, set incoming webhooks url as system environment variable like this:<br>`export SLACK_WEBHOOK=https://xxxxxxxxxx`|
|--rm|false|N/A|Remove images after scan with Trivy.|
|-q, --quiet|false|N/A|Suppress logging message.|
|--no-cache|false|N/A|***Implement in the future, so you can not use this option***<br>Disable to store cache.<br>This command does not use cache, but Trivy command use cache.|
|-h, --help|false|N/A|Show command option usage.|