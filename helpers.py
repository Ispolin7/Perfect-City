from flask import redirect, session
from functools import wraps

# if the user is logged in - it works, no - redirect to the login


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            # redirect if user not login
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function