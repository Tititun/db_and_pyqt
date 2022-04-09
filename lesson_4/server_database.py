from sqlalchemy import (create_engine, Table, Column, Integer, String,
                        MetaData, ForeignKey, DateTime, UniqueConstraint)
from sqlalchemy.orm import mapper, sessionmaker
from common.variables import SERVER_DATABASE
import datetime


class ServerStorage:

    #  таблица для хранения пользователей:
    class Users:
        def __init__(self, username):
            self.id = None
            self.name = username
            self.last_login = datetime.datetime.now()

        def __repr__(self):
            return f'User: {self.name}'

    # активные пользователи:
    class ActiveUsers:
        def __init__(self, user_id, ip_address, port):
            self.id = None
            self.user = user_id
            self.ip_address = ip_address
            self.port = port

    # история логинов пользователей:
    class LoginHistory:
        def __init__(self, user_id, date, ip, port):
            self.id = None
            self.user = user_id
            self.date_time = date
            self.ip = ip
            self.port = port

    class ContactList:
        def __init__(self, owner_id, contact_id):
            self.id = None
            self.owner_id = owner_id
            self.contact_id = contact_id


    def __init__(self):

        self.database_engine = create_engine(SERVER_DATABASE,
                                             echo=False,
                                             pool_recycle=60 * 60 * 2)

        self.metadata = MetaData()

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime)
                            )

        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'),
                                          unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   )

        user_login_history = Table('Contact_list', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String)
                                   )

        contacts = Table('Contacts', self.metadata,
                          Column('id', Integer, primary_key=True),
                          Column('owner_id', ForeignKey('Users.id')),
                          Column('contact_id', ForeignKey('Users.id')),
                          UniqueConstraint('owner_id', 'contact_id',
                                          name='contacts_unique_constraint')
                          )

        self.metadata.create_all(self.database_engine)
        mapper(self.Users, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, user_login_history)
        mapper(self.ContactList, contacts)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port):
        """записывает в базу информацию о логине пользователя"""
        print(username, ip_address, port)
        res = self.session.query(self.Users).filter_by(name=username)

        if res.count():
            user = res.first()
        else:
            user = self.Users(username)
            self.session.add(user)

        user.last_login = datetime.datetime.now()
        self.session.commit()
        self.add_to_active(user, ip_address, port)

    def add_to_active(self, user, ip_address, port):
        """добавляет пользователя в список активных"""
        new_active_user = self.ActiveUsers(user.id, ip_address, port)
        self.session.add(new_active_user)
        history = self.LoginHistory(user.id, datetime.datetime.now(),
                                    ip_address, port)
        self.session.add(history)
        self.session.commit()


    def user_logout(self, username):

        user = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def users_list(self):
        # Запрос списка пользователей.
        query = self.session.query(
            self.Users.name,
            self.Users.last_login
        )
        return query.all()

    def active_users_list(self):
        # Запрос списка активных пользователей.
        query = self.session.query(
            self.Users.name,
            self.Users.last_login,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
        ).join(self.Users)
        return query.all()

    def login_history(self, username=None):
        query = self.session.query(self.Users.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.Users)
        if username:
            query = query.filter(self.Users.name == username)
        return query.all()

    def create_contact(self, owner_id, contact_id):
        new_contact = self.ContactList(owner_id, contact_id)
        self.session.add(new_contact)
        self.session.commit()


if __name__ == '__main__':
    test_db = ServerStorage()
    test_db.user_login('Иван', '192.168.1.100', 10000)
    test_db.user_login('Марья', '192.168.1.101', 10001)

    print('Активные пользователи:')
    print(test_db.active_users_list(), end='\n\n')

    test_db.user_logout('Иван')
    print('Активные пользователи после выхода Ивана:')
    print(test_db.active_users_list(), end='\n\n')

    print('История Ивана:')
    print(test_db.login_history('Иван'), end='\n\n')

    print('Все пользователи:')
    print(test_db.users_list(), end='\n\n')
