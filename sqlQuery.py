import sqlite3
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
import csv
import io
from typing import List
import json

import logging
logging.basicConfig(filename='sqlQuery.log', level=logging.INFO)

import re

mcp = FastMCP("time")
DB_PATH = "test.db"



logger = logging.getLogger(__name__)
def __log(level, message, **kwargs):
    logger.log(level, f"{message}{"" if kwargs == {} else " | " + json.dumps(kwargs)}")


class SecurityError(Exception):
    def __init__(self, message):
        self.message = message

BLOCKED_KEYWORDS = [
    'DROP ', 'DELETE ', 'TRUNCATE ', 'ALTER ', 'CREATE ',
    'INSERT ', 'UPDATE ', 'GRANT ', 'REVOKE ', 'EXEC ',
    'EXECUTE ', 'PRAGMA ', 'ATTACH ', 'DETACH '
]

SENSITIVE_COLUMNS = {
    'users': ['password', 'ssn', 'social_security', 'tax_id'],
    'payments': ['card_number', 'cvv', 'account_number'],
    'products': [],
    'orders': [],
}

def check_sensitive_columns(query: str, table_names: List[str]):
    """Check if query attempts to access sensitive columns"""
    __log(logging.INFO, "Checking query for any sensitive columns.")
    query_lower = query.lower()
    
    for table in table_names:
        if table in SENSITIVE_COLUMNS:
            for col in SENSITIVE_COLUMNS[table]:
                patterns = [
                    rf'\b{col}\b',
                    rf'SELECT\s+.*\b{col}\b',
                    rf'\b{col}\s*=',
                ]
                for pattern in patterns:
                    if re.search(pattern, query_lower):
                        __log(logging.WARN, "Sensitive column identified!", table=table, column=col)
                        raise SecurityError(f"Access to sensitive column '{col}' in table '{table}' is not allowed")


def redact_results(results, cols, table_names: List[str]):
    """Replace sensitive data with [REDACTED]"""
    __log(logging.INFO, "Checking results for sensitive data that needs redactions.")
    if not results or not cols:
        return results
    
    sensitive_indices = set()
    col_names = [col[0].lower() for col in cols]
    
    for table in table_names:
        if table in SENSITIVE_COLUMNS:
            for sensitive_col in SENSITIVE_COLUMNS[table]:
                if sensitive_col.lower() in col_names:
                    idx = col_names.index(sensitive_col.lower())
                    sensitive_indices.add(idx)
    
    if sensitive_indices:
        __log(logging.WARN, "Redacting columns.")

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
    __log(logging.INFO, "Checking blocked keywords.")
    query_upper = query.upper()
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf'\b{keyword}\b', query_upper):
            __log(logging.WARN, "Blocked keywords identified", keyword=keyword)
            raise SecurityError(f"Operation not allowed: {keyword}")

@mcp.tool()
def get_schema():
    """
    Gets the schema for the entire database.

    Returns:
        Any the database schema.
    """
    __log(logging.INFO, "Running get_schema.")
    conn = sqlite3.connect(DB_PATH) 
    result = conn.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL;").fetchall() 
    for r in result: print(r[0], "\n") 
    conn.close()
    return result


@mcp.tool()
def execute_sql(query: str, tables: List[str]):
    """
    Executes an SQL query command

    Args:
        query (str): A query such as 'SELECT name FROM sqlite_master'.
        tables (List[str]): A list of tables being queried, e.g. ['users', 'products'].

    Returns:
        Any results from the query.
    """
    __log(logging.INFO, "Running execute_sql", query = query, tables = tables)
    check_blocked_keywords(query)
    check_sensitive_columns(query, tables)
    
    db = sqlite3.connect(DB_PATH)
    
    try:
        res = db.execute(query)
        results = res.fetchall()
        
        results = redact_results(results=results, cols=res.description, table_names=tables)
        
        return results
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

    __log(logging.INFO, "Running export_table", table=table)

    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]

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
    db = sqlite3.connect(DB_PATH)
    db.commit()
    db.close()
    


if __name__ == "__main__":
    main()

    # get_schema()
    # __log(logging.INFO, "hello?")
    # print(execute_sql("SELECT name FROM products WHERE price > 2 AND stock > 5;", tables=['products']))
    # print(execute_sql("SELECT users.name AS user_name, products.name AS product_name, orders.quantity FROM orders JOIN users ON orders.user_id = users.id JOIN products ON orders.product_id = products.id", tables=['orders']))
    # print(execute_sql("INSERT INTO users (name, email) VALUES ('jack', 'jacklynch706@gmail.com')", tables=['users']))
    # print(execute_sql("SELECT * FROM users", ['users']))