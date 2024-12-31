from setuptools import setup, find_packages

setup(
    name="podcasts-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "google-api-python-client>=2.0.0",
        "youtube-transcript-api>=0.6.0",
        "selenium>=4.0.0",
        "beautifulsoup4>=4.9.0",
        "requests>=2.25.0",
        "python-dotenv>=0.19.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "isort>=5.0.0"
        ]
    },
    entry_points={
        'console_scripts': [
            'podcasts=podcasts.main:main',
        ],
    },
    python_requires='>=3.9',
)