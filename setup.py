import setuptools

setuptools.setup(
    name="eol_course_email",
    version="0.0.1",
    author="matiassalinas",
    author_email="matsalinas@uchile.cl",
    description="Eol Course Email",
    long_description="Email between course participants",
    url="https://eol.uchile.cl",
    packages=setuptools.find_packages(),
    entry_points={
        "lms.djangoapp": [
            "eol_course_email = eol_course_email.apps:EolCourseEmailConfig",
        ],
        "openedx.course_tab": [
            "eol_course_email = eol_course_email.plugins:EolCourseEmailTab",
        ]
    },
)
