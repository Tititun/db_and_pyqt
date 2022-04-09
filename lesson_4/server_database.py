from sqlalchemy import (create_engine, Column, Integer, String,
                        ForeignKey, DateTime, UniqueConstraint)
from sqlalchemy.orm import sessionmaker, declarative_base
from common.variables import SERVER_DATABASE
import datetime

Base = declarative_base()


class ServerStorage:

    #  таблица для хранения пользователей:
    class User(Base):
        __tablename__ = 'users'

        id = Column('id', Integer, primary_key=True)
        name = Column('name', String, unique=True)
        last_login = Column('last_login', DateTime)

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
        owner_id = Column('owner_id', ForeignKey('User.id'))
        contact_id = Column('contact_id', ForeignKey('User.id'))

        UniqueConstraint('owner_id', 'contact_id',
                         name='contacts_unique_constraint')

    def __init__(self):

        self.database_engine = create_engine(SERVER_DATABASE,
                                             echo=False,
                                             pool_recycle=60 * 60 * 2)

        self.metadata = Base.metadata
        self.metadata.create_all(self.database_engine)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        self.session.query(self.ActiveUser).delete()
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
