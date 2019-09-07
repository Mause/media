from main import create_app

app = create_app(
    {'TRANSMISSION_URL': 'http://novell.mause.me:9091/transmission/rpc'}
)
