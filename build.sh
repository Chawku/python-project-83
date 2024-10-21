#!/usr/bin/env bash

make install && psql -a $DATABASE_URL -f database.sql
