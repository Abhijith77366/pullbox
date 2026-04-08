import random, string, datetime

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_expiry(days):
    return datetime.datetime.utcnow() + datetime.timedelta(days=days)