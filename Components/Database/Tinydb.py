import os
import json

class TinyDB:
    def __init__(self, db_name):
        self.db_folder = 'TinyDB Database'
        self.db_name = f'{db_name}.json'
        self.db_path = os.path.join(self.db_folder, self.db_name)

        # Create the folder if it doesn't exist
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)

        # If the database file doesn't exist, create it with an empty list
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump([], f, indent=4)

        # Load the data from the file
        with open(self.db_path, 'r') as f:
            self.data = json.load(f)

    def _save(self):
        """Automatically save the current data to the file after each change."""
        with open(self.db_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    def create(self, tag, value):
        """Create or add data by tag."""
        # Check if the tag already exists
        if any(item['tag'] == tag for item in self.data):
            raise ValueError(f"Tag '{tag}' already exists.")
        self.data.append({'tag': tag, 'value': value})
        self._save()

    def read(self, tag):
        """Read value by tag."""
        for item in self.data:
            if item['tag'] == tag:
                return item['value']
        raise ValueError(f"Tag '{tag}' not found.")

    def update(self, tag, new_value):
        """Update value by tag."""
        for item in self.data:
            if item['tag'] == tag:
                item['value'] = new_value
                self._save()
                return
        raise ValueError(f"Tag '{tag}' not found.")

    def delete(self, tag):
        """Delete data by tag."""
        for item in self.data:
            if item['tag'] == tag:
                self.data.remove(item)
                self._save()
                return
        raise ValueError(f"Tag '{tag}' not found.")

    def reset_db(self):
        """Reset the database (clear all data) and delete the database file."""
        self.data = []
        # Delete the .json file
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

# Example Usage:
# db = TinyDB('mydb')
# db.create('user', 'Not good rihanna.')
# db.create('assistant', "You're referring to Rihanna, the famous singer...")
# print(db.read('user'))  # Output: Not good rihanna.
# db.update('user', 'Better now.')
# db.delete('assistant')
# db.reset_db()  # This will clear all data and delete the .json file
