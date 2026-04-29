"""Entry point to run the Silvies Club app locally."""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
