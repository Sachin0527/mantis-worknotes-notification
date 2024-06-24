import io
import json
import pymysql
from PIL import Image


def get_connection():
    # Read the JSON file
    with open('config.json', 'r') as file:
        config = json.load(file)

    config['cursorclass'] = pymysql.cursors.DictCursor

    # Connect to the database using the configuration
    connection = pymysql.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database'],
        charset=config['charset'],
        cursorclass=config['cursorclass']
    )
    return connection


def fetch_attachments(attachment_id, bug_id, bug_note_id=None):
    print(attachment_id)
    try:
        # Connect to the database
        connection = get_connection()

        # SQL query to retrieve attachment information
        with connection.cursor() as cursor:
            sql = "SELECT filename, content FROM mantis_bug_file_table WHERE id = %s AND bug_id = %s"
            params = [attachment_id, bug_id]
            if bug_note_id is not None:
                sql += " AND bugnote_id = %s"
                params.append(bug_note_id)

            cursor.execute(sql, tuple(params))
            attachments = cursor.fetchall()

            # Process attachments (e.g., download or return file paths)
            if not attachments:
                return "No attachments found for the given criteria."
            else:
                results = []
                for attachment in attachments:
                    filename = attachment['filename']
                    content = attachment['content']
                    image = Image.open(io.BytesIO(content))

                    # Save the image as PNG
                    image.save("attachments//" +filename, format='PNG')
                    results.append(f"Image saved as {filename}")
                return results
    except pymysql.Error as e:
        print(f"Error accessing database: {e}")
    finally:
        if connection:
            connection.close()

print(fetch_attachments(1,1,8))