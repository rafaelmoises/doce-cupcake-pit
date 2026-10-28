import os

from app import create_app
from app.seed import seed

app = create_app()

with app.app_context():
    if os.environ.get("AUTO_SEED", "1") == "1":
        seed()

if __name__ == "__main__":
    app.run(debug=True)
