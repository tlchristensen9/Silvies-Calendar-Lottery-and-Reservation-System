"""WSGI entry point for PythonAnywhere deployment.

In PythonAnywhere, set the WSGI file to point here:
    from wsgi import app as application
"""

from app import create_app

app = create_app()
