import os


def seed():
    from rarbg_local.wsgi import app
    from rarbg_local.db import User, Role, db

    with app.app_context():
        user = User(
            username='Mause',
            password=app.user_manager.hash_password('password'),
            roles=[Role(name='Admin'), Role(name='Member')],
        )
        db.session.add(user)
        db.session.commit()


print({k: v for k, v in os.environ if 'HEROKU' in k})


if 'IS_REVIEW_APP' in os.environ:
    print('seeding db')
    seed()
else:
    print('not seeding db')
