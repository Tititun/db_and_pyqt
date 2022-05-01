from sqlalchemy import (create_engine, Column, Integer, String,
                        ForeignKey, DateTime, UniqueConstraint, Text)
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime
import configparser

Base = declarative_base()


class ServerStorage:

    #  таблица для хранения пользователей:
    class User(Base):
        __tablename__ = 'users'

        id = Column('id', Integer, primary_key=True)
        name = Column('name', String, unique=True)
        last_login = Column('last_login', DateTime)
        passwd_hash = Column('passwd_hash', String)

        def __repr__(self):
            return f'User: {self.name}'

    # активные пользователи:
    class ActiveUser(Base):
        __tablename__ = 'active_users'

        id = Column('id', Integer, primary_key=True)
        user = Column('user', ForeignKey('users.id'), unique=True)
        ip_address = Column('ip_address', String)
        port = Column('port', Integer)

    # история логинов пользователей:
    class LoginHistory(Base):
        __tablename__ = 'login_history'

        id = Column('id', Integer, primary_key=True)
        user = Column('user', ForeignKey('users.id'))
        date_time = Column('date_time', DateTime)
        ip = Column('ip', String)
        port = Column('port', String)

    # список контактов:
    class ContactList(Base):
        __tablename__ = 'contact_list'

        id = Column('id', Integer, primary_key=True)
        owner_id = Column('owner_id', ForeignKey('users.id'))
        contact_id = Column('contact_id', ForeignKey('users.id'))

        UniqueConstraint('owner_id', 'contact_id',
                         name='contacts_unique_constraint')

    def __init__(self, db_file):
        db_file = f'sqlite:///{db_file}'
        self.database_engine = create_engine(db_file,
                                             echo=False,
                                             pool_recycle=60 * 60 * 2,
                                             connect_args={
                                                 "check_same_thread": False})

        self.metadata = Base.metadata
        self.metadata.create_all(self.database_engine)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        self.session.query(self.ActiveUser).delete()
        # self.session.query(self.ContactList).delete()
        self.session.commit()

    def add_user(self, name, passwd_hash):
        user_row = self.User(name=name, passwd_hash=passwd_hash)
        self.session.add(user_row)
        self.session.commit()

    def remove_user(self, name):
        user = self.session.query(self.User).filter_by(name=name).first()
        self.session.query(self.ActiveUser).filter_by(user=user.id).delete()
        self.session.query(self.ContactList).filter_by(owner_id=user.id).delete()
        self.session.query(self.ContactList).filter_by(contact_id=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(user=user.id).delete()
        self.session.query(self.User).filter_by(name=name).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port):
        """записывает в базу информацию о логине пользователя"""
        res = self.session.query(self.User).filter_by(name=username)

        if res.count():
            user = res.first()
        else:
            user = self.User(name=username)
            self.session.add(user)

        user.last_login = datetime.datetime.now()
        self.session.commit()
        self.add_to_active(user, ip_address, port)

    def add_to_active(self, user, ip_address, port):
        """добавляет пользователя в список активных"""
        new_active_user = self.ActiveUser(user=user.id,
                                          ip_address=ip_address,
                                          port=port)
        self.session.add(new_active_user)
        history = self.LoginHistory(user=user.id,
                                    date_time=datetime.datetime.now(),
                                    ip=ip_address,
                                    port=port)
        self.session.add(history)
        self.session.commit()


    def user_logout(self, username):

        user = self.session.query(self.User).filter_by(name=username).first()
        self.session.query(self.ActiveUser).filter_by(user=user.id).delete()
        self.session.commit()

    def users_list(self):
        # Запрос списка пользователей.
        query = self.session.query(
            self.User.name,
            self.User.last_login
        )
        return query.all()

    def active_users_list(self):
        # Запрос списка активных пользователей.
        query = self.session.query(
            self.User.name,
            self.User.last_login,
            self.ActiveUser.ip_address,
            self.ActiveUser.port,
        ).join(self.User)
        return query.all()

    def login_history(self, username=None):
        query = self.session.query(self.User.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.User)
        if username:
            query = query.filter(self.User.name == username)
        return query.all()

    def create_contact(self, owner, contact):
        owner_id = self.session.query(self.User.id)\
            .filter(self.User.name == owner).scalar()
        contact_id = self.session.query(self.User.id) \
            .filter(self.User.name == contact).scalar()
        new_contact = self.ContactList(owner_id=owner_id, contact_id=contact_id)
        self.session.add(new_contact)
        self.session.commit()

    def delete_contact(self, owner, contact):
        owner_id = self.session.query(self.User.id)\
            .filter(self.User.name == owner).scalar()
        contact_id = self.session.query(self.User.id) \
            .filter(self.User.name == contact).scalar()
        self.session.query(self.ContactList).\
            filter(self.ContactList.owner_id==owner_id,
                   self.ContactList.contact_id==contact_id).delete()
        self.session.commit()

    def list_contacts(self, name):
        owner_id = self.session.query(self.User.id).filter(self.User.name == name).scalar()

        friends_list = self.session.query(self.User.name).\
            filter(self.ContactList.owner_id == owner_id).\
            filter(self.User.id == self.ContactList.contact_id).all()

        return [f[0] for f in friends_list] if friends_list else []

    def contacts_stats(self):
        return self.session.query(self.User.name, self.User.last_login).all()

    def check_user(self, name):
        """Метод проверяющий существование пользователя."""
        if self.session.query(self.User).filter_by(name=name).count():
            return True
        else:
            return False

    def get_hash(self, name):
        """Метод получения хэша пароля пользователя."""
        user = self.session.query(self.User).filter_by(name=name).first()
        return user.passwd_hash

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('server.ini')
    db_file = config['SETTINGS']['database_file']

    test_db = ServerStorage(db_file)
    test_db.user_login('Иван', '192.168.1.100', 10000)
    test_db.user_login('Марья', '192.168.1.101', 10001)
    test_db.user_login('Дима', '192.168.1.102', 10000)
    test_db.user_login('Таня', '192.168.1.103', 10000)
    test_db.user_login('Коля', '192.168.1.104', 10000)

    print('Активные пользователи:')
    print(test_db.active_users_list(), end='\n\n')

    test_db.user_logout('Иван')
    print('Активные пользователи после выхода Ивана:')
    print(test_db.active_users_list(), end='\n\n')

    print('История Ивана:')
    print(test_db.login_history('Иван'), end='\n\n')

    print('Все пользователи:')
    print(test_db.users_list(), end='\n\n')

    test_db.create_contact('Иван', 'Марья')
    test_db.create_contact('Иван', 'Дима')

    test_db.create_contact('Марья', 'Дима')
    test_db.create_contact('Марья', 'Иван')

    print('Контакты Ивана:')
    print(test_db.list_contacts('Иван'), end='\n\n')

    print('Удаляем Диму из контактов Ивана')
    test_db.delete_contact('Иван', 'Дима')

    print('Контакты Ивана:')
    print(test_db.list_contacts('Иван'), end='\n\n')

    print(test_db.contacts_stats())

    test_db.session.close()