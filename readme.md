# EOL Course Email

![https://github.com/eol-uchile/eol_course_email/actions](https://github.com/eol-uchile/eol_course_email/workflows/Python%20application/badge.svg)

Email between course participants

## Configurations

LMS/CMS Django Admin:

- */admin/site_configuration/siteconfiguration/*
    - **"EOL_COURSE_EMAIL_TAB_ENABLED":true**


## Translation

**Install**

    docker run -it --rm -w /code -v $(pwd):/code python:3.8 bash
    pip install -r requirements.txt
    make create_translations_catalogs
    add your translation in .po files

**Compile**

    docker run -it --rm -w /code -v $(pwd):/code python:3.8 bash
    pip install -r requirements.txt
    make compile_translations

**Update**

    docker run -it --rm -w /code -v $(pwd):/code python:3.8 bash
    pip install -r requirements.txt
    make update_translations

### File Upload Configuration

Add this configuration in `production.py`

```
## Setup COURSE_EMAIL for S3
COURSE_EMAIL_STORAGE_CLASS = {
  'class': 'storages.backends.s3boto3.S3Boto3Storage',
  'options': {
    'location': 'course_email/',
    'bucket_name': 'bucketname'
  }
}
COURSE_EMAIL_STORAGE_CLASS = ENV_TOKENS.get('COURSE_EMAIL_STORAGE_CLASS', COURSE_EMAIL_STORAGE_CLASS)
```

Fileupload max size: 10mb (customizable)


## Development Settings

Set React app url:

    EOL_COURSE_EMAIL_DEV_URL = '/eol/eol_course_email/static'


## Compile frontend (production)

    > cd frontend
    > docker build -t frontend .
    > docker run -v $(pwd)/dist:/app/dist frontend npm run-script build
    > rm ../eol_course_email/static/eol_course_email/*
    > cp -r dist/* ../eol_course_email/static/eol_course_email/

## TESTS
**Prepare tests:**

    > cd .github/
    > docker-compose run --rm lms /openedx/requirements/eol_course_email/.github/test.sh
