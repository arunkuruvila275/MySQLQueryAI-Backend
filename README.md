
# MySQLQueryAI Backend

MySQLQueryAI Backend is a FastAPI application that uses OpenAI's GPT-4-turbo model to translate natural language queries into SQL queries, execute them on a MySQL database, and explain SQL queries in natural language.

## Features

- **Database Connection**: Connect to a MySQL database with provided credentials.
- **Structure Fetching**: Retrieve and store the structure of all tables, including indexes.
- **Natural Language Querying**: Convert natural language queries into efficient SQL queries using OpenAI API.
- **Query Execution**: Execute generated SQL queries and return results.
- **Query Explanation**: Explain SQL queries in natural language.

## Prerequisites

- Python 3.7+
- MySQL database
- OpenAI API key

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/mysqlqueryai-backend.git
    cd mysqlqueryai-backend
    ```

2. Create a virtual environment and activate it:
    ```sh
    python3 -m venv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up your environment variables. Create a `.env` file in the root of the project and add your OpenAI API key:
    ```sh
    OPENAI_API_KEY=your_openai_api_key
    ```

## Configuration

The configuration for the database connection is handled via environment variables. Ensure that the `.env` file contains the necessary configuration.

## Usage

1. Start the FastAPI server:
    ```sh
    uvicorn app.main:app --reload
    ```

2. The API will be available at `http://localhost:8000`.

## API Endpoints

### Connect to Database

- **Endpoint**: `/connect/`
- **Method**: `POST`
- **Request Body**:
    ```json
    {
        "username": "your_db_username",
        "password": "your_db_password",
        "hostname": "your_db_hostname",
        "database": "your_db_name"
    }
    ```
- **Response**:
    ```json
    {
        "message": "Connection successful"
    }
    ```

### Translate Natural Language Query to SQL

- **Endpoint**: `/translate_query/`
- **Method**: `POST`
- **Request Body**:
    ```json
    {
        "natural_language_query": "your natural language query",
        "connection_details": {
            "username": "your_db_username",
            "password": "your_db_password",
            "hostname": "your_db_hostname",
            "database": "your_db_name"
        }
    }
    ```
- **Response**:
    ```json
    {
        "sql_query": "generated SQL query"
    }
    ```

### Execute SQL Query

- **Endpoint**: `/execute_query/`
- **Method**: `POST`
- **Request Body**:
    ```json
    {
        "sql_query": "your SQL query",
        "connection_details": {
            "username": "your_db_username",
            "password": "your_db_password",
            "hostname": "your_db_hostname",
            "database": "your_db_name"
        }
    }
    ```
- **Response**:
    ```json
    {
        "result": "query result as list of dictionaries"
    }
    ```

### Explain SQL Query

- **Endpoint**: `/explain_query/`
- **Method**: `POST`
- **Request Body**:
    ```json
    {
        "sql_query": "your SQL query"
    }
    ```
- **Response**:
    ```json
    {
        "explanation": "natural language explanation of the SQL query"
    }
    ```

## Project Structure

```
mysqlqueryai-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py             # Main FastAPI application
│   ├── database.py         # Database connection and setup
│   └── models.py           # SQLAlchemy models
│
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [OpenAI API](https://beta.openai.com/docs/)
