import sqlite3
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
import csv
import io
from typing import List
import os

import logging
logging.basicConfig(filename='sqlQuery.log', level=logging.INFO)

from dotenv import load_dotenv
import re

mcp = FastMCP("time")

load_dotenv()


class SecurityError(Exception):
    def __init__(self, message):
        self.message = message

DB_PATH = os.getenv("DATABASE_PATH")

from logger import logger as log

BLOCKED_KEYWORDS = [
    'DROP ', 'DELETE ', 'TRUNCATE ', 'ALTER ', 'CREATE ',
    'INSERT ', 'UPDATE ', 'GRANT ', 'REVOKE ', 'EXEC ',
    'EXECUTE ', 'PRAGMA ', 'ATTACH ', 'DETACH ', 'IIF', 
    'CASE', 'JSON_OBJECT', 'FORMAT', 'PRINTF'
]

SENSITIVE_COLUMNS = {
    'users': ['password', 'ssn', 'social_security', 'tax_id'],
    'payments': ['card_number', 'cvv', 'account_number'],
    'products': [],
    'orders': [],
}

def check_sensitive_columns(columns: str, tables: List[str]):
    """Check if query attempts to access sensitive columns"""
    log.debug("Checking query for any sensitive columns.")

    for table in tables: 
        if table in SENSITIVE_COLUMNS:
            for col in columns:
                if col in SENSITIVE_COLUMNS[table]:
                    log.critical(f"Sensitive column identified: '{col}'")
                    raise SecurityError(f"Access to sensitive column '{col}' in table '{table}' is not allowed")


def redact_results(results, cols, table_names):
    """Replace sensitive data with [REDACTED]"""
    log.debug("Checking results for sensitive data that needs redactions.")
    if not results or not cols:
        return results
    
    
    sensitive_indices = set()
    
    for table in table_names:
        if table in SENSITIVE_COLUMNS:
            for sensitive_col in SENSITIVE_COLUMNS[table]:
                for col in cols:
                    if sensitive_col.lower() in col:
                        log.warning(f'Sensitive results: {col}')
                        sensitive_indices.add(cols.index(col))
    
    if sensitive_indices:
        log.warning("Redacting columns.")

        redacted_results = []
        for row in results:
            new_row = list(row)
            for idx in sensitive_indices:
                new_row[idx] = '[REDACTED]'
            redacted_results.append(tuple(new_row))
        return redacted_results
    
    return results

def check_blocked_keywords(query: str):
    """Check for dangerous SQL keywords"""
    log.debug("Checking blocked keywords.")
    query_upper = query.upper()
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf'{keyword}', query_upper):
            log.critical(f"Blocked keywords identified '{keyword}'")
            raise SecurityError(f"Operation not allowed: {keyword}")

@mcp.tool()
def get_schema():
    """
    Gets the schema for the entire database.

    Returns:
        Any the database schema.
    """
    log.debug("Running get_schema.")
    conn = sqlite3.connect(DB_PATH) 
    results = conn.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL;").fetchall() 

    toReturn = []
    
    for table in results:
        returnTable = []
        columns = table[0].split('\n')
        returnTable.append(columns[0])
        quoteStart = columns[0][:].find("TABLE ")+6
        quoteEnd = columns[0][quoteStart+1:].find("(")
        table_name = columns[0][quoteStart:quoteStart+quoteEnd]
        for column in columns[1:]:
            print(column)
            if table_name in SENSITIVE_COLUMNS:
                for restricted in SENSITIVE_COLUMNS[table_name]:
                    print(restricted)
                    if column.startswith(restricted):
                        pass
                    else: returnTable.append(column)
            else: returnTable.append(column)
        toReturn.append(set(returnTable))


    conn.close()
    log.debug("Returning schema")

    return toReturn


@mcp.tool()
def execute_sql(query: str):
    """
    Executes an SQL query command

    Args:
        query (str): A query such as 'SELECT name FROM sqlite_master'.
        tables (List[str]): A list of tables being queried, e.g. ['users', 'products'].

    Returns:
        Any results from the query.
    """

    log.debug(f"Running execute_sql '{query}'")
    check_blocked_keywords(query)

    #(?<=SELECT\s)([0-9a-zA-Z]+)((,\s?([0-9a-z]+))*)
    #(?<=FROM\s)([0-9a-zA-Z]+)((,\s?([0-9a-z]+))*)
    columns = [col[0].split(',') for col in re.findall(r"(?<=SELECT\s)(([0-9a-zA-Z._()]+)(((,?\s?([0-9a-zA-Z._()]+))|(\sAS\s([a-z0-9A-Z._()]+)))*)|([*]))", query)][0]
    tables = [table[0] for table in re.findall(r"(?<=FROM\s)([0-9a-zA-Z._()]+)((,\s?([0-9a-z._()]+))*)(((\sJOIN\s)(([a-zA-Z0-9._()]+)\sON\s([a-zA-Z0-9._()]+)\s?=\s?[a-zA-Z0-9._()]+))*)?", query)]

    print(f"cols: {columns}")
    check_sensitive_columns(columns=columns, tables=tables)
    
    db = sqlite3.connect(DB_PATH)
    
    try:
        res = db.execute(query)
        results = res.fetchall()
        if columns == ['*']:
            cols = [col[0] for col in res.description]
            toReturn = redact_results(results=results, cols=cols, table_names=tables)
            log.debug(f"Query results: {results}")
            db.close()
            return toReturn
        else: 
            toReturn = redact_results(results=results, cols=columns, table_names=tables)
            log.debug(f"Query results: {results}")
            db.close()
            return toReturn
    finally:
        db.close()

@mcp.tool()
def export_table_csv(table: str):
    """
    Returns a .csv data of a SQL table. After getting the CSV data, you MUST create a new text/csv artifact so the user can download it directly.

    Args:
        table (str): The name of the table to be returned.

    Returns:
        A csv representation of the database.
    """

    log.debug(f"Exportin table: {table}")

    db = sqlite3.connect(DB_PATH)    
    try:
        res = db.execute(f"SELECT * FROM {table}")
        results = res.fetchall()
        columns = [description[0] for description in res.description]
        rows = redact_results(results=results, cols=columns, table_names=[table])
        file = io.StringIO()
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)
        csv_data = file.getvalue()
        
        return [
            TextContent(
                type="text",
                text=f"CSV export of '{table}' table is ready."
            ),
            TextContent(
                type="text",
                text=csv_data
            )
        ]
    finally:
        db.close()




def main():
    # Initialize and run the server
    mcp.run(transport='stdio')
    


if __name__ == "__main__":
    main()

    # print(get_schema())
    # log.info("hello?")
    # print(execute_sql("SELECT name FROM products WHERE price > 2 AND stock > 5;"))
    # print(execute_sql("SELECT users.name AS user_name, products.name AS product_name, orders.quantity, completed FROM orders JOIN users ON orders.user_id = users.id JOIN products ON orders.product_id = products.id"))
    # print(execute_sql("INSERT INTO users (name, email) VALUES ('jack', 'jacklynch706@gmail.com')"))
    # print(execute_sql("SELECT name, users.password AS pswd, email FROM users"))
    # print(execute_sql("SELECT * FROM users"))
    # print(execute_sql("SELECT UPPER(password) FROM users"))
    # print(execute_sql("SELECT format('%s', password) FROM users"))
    # print(execute_sql("SELECT printf('%s', password) FROM users"))
    # print(execute_sql("SELECT IIF(id > 0, password, 'x') FROM users"))
    # print(execute_sql("SELECT * FROM users GROUP BY password"))

    # print(export_table_csv('users'))