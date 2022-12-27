from setuptools import setup

setup(name='beanprice_treasury',
      version='0.1',
      description='Fetch US Treasury prices for beanprice module',
      url='https://github.com/xinluh/beanprice_treasury',
      author='Xinlu',
      author_email='',
      license='MIT',
      packages=['beanprice_treasury'],
      install_requires=[
          'beancount>=2.3.4',
          'requests',
      ],
      python_requires='>=3.6'
)
