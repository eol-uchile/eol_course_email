import os
from setuptools import setup


def package_data(pkg, roots):
    """Generic function to find package_data.

    All of the files under each of the `roots` will be declared as package
    data for package `pkg`.

    """
    data = []
    for root in roots:
        for dirname, _, files in os.walk(os.path.join(pkg, root)):
            for fname in files:
                data.append(os.path.relpath(os.path.join(dirname, fname), pkg))

    return {pkg: data}

setup(
    name="eol_course_email",
    version="0.0.1",
    author="matiassalinas",
    author_email="matsalinas@uchile.cl",
    description="Eol Course Email",
    long_description="Email between course participants",
    url="https://eol.uchile.cl",
    packages=[
        'eol_course_email',
    ],
    package_data=package_data("eol_course_email", ["static", "public", "locale"]),
    entry_points={
        "lms.djangoapp": [
            "eol_course_email = eol_course_email.apps:EolCourseEmailConfig",
        ],
        "openedx.course_tab": [
            "eol_course_email = eol_course_email.plugins:EolCourseEmailTab",
        ]
    },
)
