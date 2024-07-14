from setuptools import setup, find_packages

setup(
    name='mantis-worknotes-notification',
    version='0.0.1',
    description='It extracts worknotes from mantis based on last update timestamp and send it to MSMQ for further email trigger',
    url='https://github.com/Sachin0527/mantis-worknotes-notification.git',
    author='Karan Gupta, Sachin Kumar',
    author_email='karangupta125@gmail.com',
    packages=find_packages(),
    install_requires=[],
)