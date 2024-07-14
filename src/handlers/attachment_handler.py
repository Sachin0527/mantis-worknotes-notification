import os, io, pymysql
from PIL import Image

from src.config.config import MysqlConfig


def get_attachments_from_db(connection, bug_id, bug_note_id=None):
    # SQL query to retrieve attachment information
    with connection.cursor() as cursor:
        sql = "SELECT filename, content FROM mantis_bug_file_table WHERE bug_id = %s"
        params = [bug_id]
        if bug_note_id is not None:
            sql += " AND bugnote_id = %s"
            params.append(bug_note_id)
        else:
            sql += " AND bugnote_id is NULL"

        cursor.execute(sql, tuple(params))
        attachments = cursor.fetchall()
    return attachments


class AttachmentHandler:
    def __init__(self, mysql_config, attachment_base_dir):
        self.__config = MysqlConfig(mysql_config)
        self.__attachment_base_dir = attachment_base_dir

    def get_connection(self):
        # Connect to the database using the configuration
        connection = pymysql.connect(
            host=self.__config.host,
            user=self.__config.user,
            password=self.__config. password,
            database=self.__config.database,
            charset=self.__config.charset,
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection

    def download_attachments(self, attachments, bug_id, bug_note_id):
        results = []
        try:
            for attachment in attachments:
                filename = attachment['filename']
                content = attachment['content']
                image = Image.open(io.BytesIO(content))

                # Create directories if they do not exist
                bug_folder = os.path.join(self.__attachment_base_dir, f"bug_{bug_id}")
                note_folder = os.path.join(bug_folder, f"note_{bug_note_id}") if bug_note_id else bug_folder
                os.makedirs(note_folder, exist_ok=True)

                # Save the image as PNG in the appropriate folder
                save_path = os.path.join(note_folder, filename)
                image.save(save_path, format='PNG')
                absolute_path = os.path.abspath(save_path)
                results.append(absolute_path)
            return results
        except IOError as e:
            raise Exception(f"An error occurred while downloading attachments: {e}")

    def fetch_attachments(self, bug_id, bug_note_id=None):
        connection = None
        try:
            # Connect to the database
            connection = self.get_connection()
            attachments = get_attachments_from_db(connection, bug_id, bug_note_id)
            if attachments:
                results = self.download_attachments(attachments, bug_id, bug_note_id)
                return results
        except pymysql.Error as e:
            raise Exception(f"An unexpected error occurred while fetching attachment from mysql DB: {e}")
        finally:
            if connection:
                connection.close()