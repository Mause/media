import os


def seed():
    from rarbg_local.db import Role, User, db
    from rarbg_local.wsgi import _app

    with _app.app_context():
        user = User(
            username='Mause',
            password=_app.user_manager.hash_password('password'),
            roles=[Role(name='Admin'), Role(name='Member')],
        )
        db.session.add(user)
        db.session.commit()


if 'IS_REVIEW_APP' in os.environ:
    print('seeding db')
    seed()
else:
    print('not seeding db')
