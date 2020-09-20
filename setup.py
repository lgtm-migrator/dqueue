from setuptools import setup

setup(name='dda-queue',
      version='1.1.22-dev0',
      description='a queue manager (yet another)',
      author='Volodymyr Savchenko',
      author_email='vladimir.savchenko@gmail.com',
      license='MIT',
      packages=['dqueue'],
      entry_points={
          'console_scripts':  [
              'dqueue=dqueue.cli:main',
                ]
          },
      install_requires=[
          'marshmallow',
          'apispec',
          'flasgger',
          'bravado',
          'termcolor',
          'pymysql',
          'peewee',
          'retrying',
          'oda-knowledge-base[cwl]>=0.6.18', # should be an option
          'jwt',
          ],
      zip_safe=False,
     )
