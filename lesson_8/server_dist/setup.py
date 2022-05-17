from setuptools import setup, find_packages

setup(name="py_danil_server",
      version="0.0.3",
      description="Server app",
      author="Danil Mosin",
      author_email="vinniopo@mail.ru",
      packages=find_packages(),
      include_package_data=True,
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex'],
      scripts=['server/server_run']
      )
