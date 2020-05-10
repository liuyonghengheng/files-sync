from setuptools import setup

setup(
    name='files_sync',
    version='0.0.1',
    description='files remote sync',
    long_description='files remote sync base on watchdog and ssh',
    install_requires=[
        'apache-airflow',
        'watchdog'
    ],
    python_requires='>=3.6'
)
