import yaml


# Config class to hold the mandatory MySQL variables
class MysqlConfig:
    def __init__(self, config):
        self.host = config['host']
        self.user = config['user']
        self.password = config['password']
        self.database = config['database']
        self.charset = config['charset']


# Config class to hold the mandatory Mantis variables
class MantisConfig:
    def __init__(self, config):
        self.base_url = config['base_url']
        self.api_token = config['api_token']
        self.project_id = config['project_id']
        self.time_zone = config['time_zone']
        self.issue_fields = [field.strip() for field in config['issue_fields'].split(',')]
        self.work_notes_fields = [field.strip() for field in config['work_notes_fields'].split(',')]
        self.filter_id = config['filter_id']


# Reads YAML config file from given path.
# Returns the specific section content if supplied in method call or returns overall file content
def read_config(file_path, target_section=None):
    try:
        with open(file_path, 'r') as file:
            content = yaml.safe_load(file)
            if content is None:
                raise ValueError("YAML file is empty")
            if target_section:
                if target_section in content:
                    return content[target_section]
                else:
                    raise KeyError(f"Section '{target_section}' not found in the YAML file")
            else:
                return content
    except FileNotFoundError:
        raise Exception(f"Error: The file '{file_path}' was not found.")
    except yaml.YAMLError as e:
        raise Exception(f"Error parsing YAML file: {e}")
    return None
