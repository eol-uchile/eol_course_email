# EOL Course Email

![https://github.com/eol-uchile/eol_course_email/actions](https://github.com/eol-uchile/eol_course_email/workflows/Python%20application/badge.svg)

Email between course participants

## Configurations

LMS Django Admin:

- */admin/site_configuration/siteconfiguration/*
    - **"EOL_COURSE_EMAIL_TAB_ENABLED":true**


## Development Settings

Set React app url:

    EOL_COURSE_EMAIL_DEV_URL = '/eol/eol_course_email/static'


## Compile frontend (production)

    > cd frontend
    > docker build -t frontend .
    > docker run -v $(pwd)/dist:/app/dist frontend npm run-script build
    > cp -r dist/* ../eol_course_email/static/eol_course_email/

## TESTS
**Prepare tests:**

    > cd .github/
    > docker-compose run --rm lms /openedx/requirements/eol_course_email/.github/test.sh
