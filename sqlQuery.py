import sqlite3
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
import csv
import io
from typing import List

mcp = FastMCP("time")
DB_PATH = "test.db"


@mcp.tool()
def get_schema():
    """
    Returns:
        Any the database schema.
    """
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    schema_info = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        schema_info[table_name] = [
            {
                "name": col[1],
                "type": col[2],
                "notnull": bool(col[3]),
                "pk": bool(col[5])
            }
            for col in columns
        ]
    
    db.close()
    return schema_info

@mcp.tool()
def execute_sql(query: str):
    """
    Executes an SQL query

    Args:
        query (str): A query such as 'SELECT name FROM sqlite_master'.

    Returns:
        Any results from the query.
    """
    db = sqlite3.connect(DB_PATH)
    res = db.execute(query)
    toReturn = res.fetchall()
    db.commit()
    db.close()
    return toReturn

@mcp.tool()
def export_table_csv(table: str):
    """
    Returns a .csv data of a SQL table. After getting the CSV data, you MUST create a new text/csv artifact so the user can download it directly.

    Args:
        table (str): The name of the table to be returned.

    Returns:
        A csvc representation of the database.
    """
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]

    file = io.StringIO()
    writer = csv.writer(file)
    writer.writerow(columns)
    writer.writerows(rows)
    csv_data = file.getvalue()
    db.close()
    return [
        TextContent(
            type="text",
            text=f"""CSV export of '{table}' table is ready. Save this as a .csv file and make it ready for download.
            Don't ask me to copy and save these as .csv files. Make them ready for download. I just want to click on a link and download it.
            Dont make an interactive artifact, just a downloadable file. Save this as {table}.csv:\n\n{csv_data}"""
        ),
        TextContent(
            type="text",
            text=csv_data
        )
    ]

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')
    db = sqlite3.connect(DB_PATH)
    db.commit()
    db.close()


if __name__ == "__main__":
    main()