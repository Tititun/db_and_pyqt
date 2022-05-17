from setuptools import setup, find_packages

setup(name="py_danil_client",
      version="0.0.1",
      description="Client app",
      author="Danil Mosin",
      author_email="vinniopo@mail.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex'],
      scripts=['client/client_run']
      )
