#!/bin/bash

# Script should be run from within the `tests` directory to set up the defog.ai
# database with the tables that are used by the various schemas. The e2e
# defog tests cannot be run unless this commmand has already been used to set
# up the sqlite database.

set -eo pipefail

rm -fv defog.db
sqlite3 defog.db < init_defog.sql

rm -fv Broker.db
sqlite3 Broker.db < broker_sqlite.sql

rm -fv Dealership.db
sqlite3 Dealership.db < dealership_sqlite.sql

rm -fv Ewallet.db
sqlite3 Ewallet.db < ewallet_sqlite.sql

rm -fv DermTreatment.db
sqlite3 DermTreatment.db < derm_treatment_sqlite.sql
