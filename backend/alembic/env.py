from app.database import Base
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from app.models.metric_anomaly import MetricAnomaly
from app.core.config import settings
from app.models.daily_cost_snapshot import DailyCostSnapshot
from app.database import Base
from app.models.resource_metric_snapshot import ResourceMetricSnapshot
from app.models.optimization_recommendation import (
    OptimizationRecommendation,
)

# Models import hona zaroori hai,
# tabhi tables Base.metadata mein register hongi
from app.models import CloudResource, User


# Alembic configuration object 
config = context.config


# .env ka MySQL URL Alembic configuration mein set karo
# %% conversion password mein % character hone ki condition handle karta hai
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url.replace("%", "%%")
)


# Alembic logging configuration
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# SQLAlchemy models ka metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Database connection create kiye bina migration SQL generate karta hai.
    """

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Actual MySQL connection ke saath migration execute karta hai.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()