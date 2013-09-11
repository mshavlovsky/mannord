from setuptools import setup

setup(name='mannord',
      version='0.1',
      description='Reputation system (spam flagging as for now)',
      url='https://github.com/mshavlovsky/mannord',
      author='Michael Shavlovsky',
      author_email='mshavlovsky@gmail.com',
      license='BSD',
      packages=['mannord'],
      long_description=open('README.txt').read(),
      package_data = { 'mannord': ['mannord.conf'] }
      )
