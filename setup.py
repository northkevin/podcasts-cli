from setuptools import setup, find_packages

setup(
    name="podcasts-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic",
        "google-api-python-client",
        "youtube-transcript-api",
        "selenium",
        "beautifulsoup4",
        "requests"
    ],
    entry_points={
        'console_scripts': [
            'podcasts=podcasts.main:main',
        ],
    },
    python_requires='>=3.9',
)