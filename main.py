from logger_util import get_logger
import settings
from src import app

log = get_logger(__name__)


if __name__ == '__main__':
    log.info(f"Start Running as debug mode.....")
    app.run(debug=False, port=settings.FLASK_SERVER_PORT)
else:
    log.info(f"Start Running.....")
