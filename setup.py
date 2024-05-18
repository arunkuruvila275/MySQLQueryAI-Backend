from setuptools import setup, find_packages

setup(
    name="mysqlqueryai-backend",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "sqlalchemy",
        "pydantic",
        "openai",
        "uvicorn",
        "pymysql",
        "setuptools"
    ],
    entry_points={
        'console_scripts': [
            'start-mysqlqueryai-backend=app.main:main',
        ],
    },
)