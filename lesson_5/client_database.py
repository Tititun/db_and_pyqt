from sqlalchemy import (create_engine, Column, Integer, String, DateTime, or_)
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


class ClientStorage:

    #  таблица для хранения контактов:
    class Contact(Base):
        __tablename__ = 'contacts'

        id = Column('id', Integer, primary_key=True)
        name = Column('name', String, unique=True)

    # табллица для хранения сообщений:
    class Message(Base):
        __tablename__ = 'messages'

        id = Column('id', Integer, primary_key=True)
        from_user = Column('from_user', String)
        to_user = Column('to_user', String)
        message = Column('message', String)
        date_time = Column('date_time', DateTime)


    def __init__(self, user):
        database = f'sqlite:///client_{user}.db3'
        self.user = user
        self.database_engine = create_engine(database,
                                             echo=False,
                                             pool_recycle=60 * 60 * 2,
                                             connect_args={
                                                 "check_same_thread": False}
                                             )

        self.metadata = Base.metadata
        self.metadata.create_all(self.database_engine)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        # self.session.query(self.Contact).delete()
        # self.session.query(self.Message).delete()
        # self.session.commit()

    def add_contact(self, name):
        """записывает в базу новый контакт"""
        new_contact = self.Contact(name=name)
        self.session.add(new_contact)
        self.session.commit()

    def delete_contact(self, name):
        self.session.query(self.Contact).filter(self.Contact.name == name)\
            .delete()
        self.session.commit()

    def list_contacts(self):
        return [c[0] for c in self.session.query(self.Contact.name)]

    def write_message(self, from_, to_, text, datetime_):
        new_message = self.Message(from_user=from_, to_user=to_,
                                   message=text, date_time=datetime_)
        self.session.add(new_message)
        self.session.commit()

    def get_history(self, contact):
        query = self.session.query(self.Message)\
            .filter(or_(self.Message.from_user == contact,
                         self.Message.to_user == contact))
        return [(history_row.from_user, history_row.to_user,
                 history_row.message, history_row.date_time)
                for history_row in query.all()]


if __name__ == '__main__':
    username = 'Test'
    test_db = ClientStorage(username)

    test_db.add_contact('Friend 1')
    test_db.add_contact('Friend 2')
    test_db.add_contact('Friend 3')

    print('Список контактов:')
    print(test_db.list_contacts(), end='\n\n')

    print('Удаляем первый контакт', end='\n\n')
    test_db.delete_contact('Friend 1')

    print('Список контактов после удаления:')
    print(test_db.list_contacts(), end='\n\n')
