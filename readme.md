# EOL Course Email

![https://github.com/eol-uchile/eol_course_email/actions](https://github.com/eol-uchile/eol_course_email/workflows/Python%20application/badge.svg)

Email between course participants

## Configurations

LMS Django Admin:

- */admin/site_configuration/siteconfiguration/*
    - **"EOL_COURSE_EMAIL_TAB_ENABLED":true**

## TESTS
**Prepare tests:**

    > cd .github/
    > docker-compose run --rm lms /openedx/requirements/eol_course_email/.github/test.sh
