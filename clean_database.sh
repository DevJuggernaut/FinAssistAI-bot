#!/bin/bash
# Script to clean the finance_bot database

echo "This script will clear all data from the finance_bot database."
echo "Only the default categories will be preserved."
echo "Are you sure you want to continue? (y/n)"

read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
then
    echo "Cleaning database..."
    psql postgresql://abobina:2323@localhost:5432/finance_bot -f clean_database.sql
    echo "Database has been cleaned."
else
    echo "Operation cancelled."
fi
