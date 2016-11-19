import os

__all__ = (
    "BASE_ENVIRONMENT",
    "CONTROL_ENVIRONMENT",
    "DEVELOPMENT_ENVIRONMENT",
    "ENVIRONMENTS",
    "EXIT_ENV",
    "EXIT_INPUT",
    "EXIT_OK",
    "EXIT_OTHER",
    "EXIT_USAGE",
    "PROJECT_HOME",
    "TESTING_ENVIRONMENT",
    "STAGING_ENVIRONMENT",
    "LIVE_ENVIRONMENT",
)

# Standard environments.
BASE_ENVIRONMENT = "base"
CONTROL_ENVIRONMENT = "control"
DEVELOPMENT_ENVIRONMENT = "development"
TESTING_ENVIRONMENT = "testing"
STAGING_ENVIRONMENT = "staging"
LIVE_ENVIRONMENT = "live"

ENVIRONMENTS = (
    BASE_ENVIRONMENT,
    CONTROL_ENVIRONMENT,
    DEVELOPMENT_ENVIRONMENT,
    TESTING_ENVIRONMENT,
    STAGING_ENVIRONMENT,
    LIVE_ENVIRONMENT,
)

# Exit codes.
EXIT_OK = 0
EXIT_USAGE = 1
EXIT_INPUT = 2
EXIT_ENV = 3
EXIT_OTHER = 4

# Location of projects.
PROJECT_HOME = os.environ.get("PROJECT_HOME", "~/Work")