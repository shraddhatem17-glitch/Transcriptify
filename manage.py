from flask.cli import with_appcontext
from flask_migrate import Migrate
from src import app, db
import click

# Set up migration
migrate = Migrate(app, db)

# --- Custom CLI commands ---


@click.command("create-db")
@with_appcontext
def create_db():
    """Creates the db tables."""
    db.create_all()


@click.command("drop-db")
@with_appcontext
def drop_db():
    """Drops the db tables."""
    db.drop_all()
    db.session.commit()


@click.command("recreate-db")
@with_appcontext
def recreate_db():
    """Drops and re-creates the db tables."""
    db.drop_all()
    db.create_all()
    db.session.commit()


@click.command("init-db-tables")
@with_appcontext
def init_db_tables():
    """Inserts initial data (like roles, etc)."""
    print("done")  # Replace with actual inserts


@click.command("set-up-env")
@with_appcontext
def set_up_env():
    """Sets up environment and creates initial tables."""
    create_db.invoke(ctx=None)
    init_db_tables.invoke(ctx=None)



