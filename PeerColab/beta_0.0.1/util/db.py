"""
PeerColab

Python file facilitating database management and authentication

Copyright Joan Chirinos, 2021.
"""

from typing import Tuple
import uuid
# import datetime

import sqlite3
from scrypt import scrypt


class DBManager:

    def __init__(self, filename: str, table_defns_filename: str) -> None:
        """
        Initialize DBManager class.

        Parameters
        ----------
        filename : str
            filename for current database
        table_defns_filename : str
            filename for file containing table definition strings

        Returns
        -------
        None

        """
        self.db_filename = filename
        self.table_defns_filename = table_defns_filename

    def create_db(self) -> None:
        """
        Create database.

        Returns
        -------
        None

        """
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        with open(self.table_defns_filename) as f:
            for defn in f.readlines():
                print(defn[:-1])
                if defn.strip() != '':
                    c.execute(defn)

        db.commit()
        db.close()

    def register_user(self, email: str, password: str,
                      first_name: str, last_name: str,
                      teacher: int) -> bool:
        """
        Register new user to DB

        Parameters
        ----------
        email : str
            the user's email
        password : str
            the user's password
        first_name: str
            the user's first name
        last_name: str
            the user's last name
        teacher: int
            1 if user is teacher, 0 otherwise

        Returns
        -------
        bool
            True if user got registered.
            False if user already exists.

        """
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        # Check if email is already registered
        if c.execute('SELECT first FROM users WHERE email=?',
                     (email,)).fetchone():
            print('returning false')
            return False

        # Register user
        salt = str(uuid.uuid4())

        hash = scrypt.hash(password, salt)

        c.execute('INSERT INTO users VALUES(?,?,?,?,?,?)',
                  (email, hash, salt, first_name, last_name, teacher))

        db.commit()
        db.close()

        return True

    def authenticate_user(self, email: str, password: str) -> bool:
        """
        Authenticate user with given password.

        Parameters
        ----------
        email : str
            the user's email.
        password : str
            the user's password.

        Returns
        -------
        bool
            True if password matches email.
            False if email doesn't exist or password doesn't match email.

        """
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        c.execute('SELECT hash, salt FROM users WHERE email=?', (email,))

        vals = c.fetchone()
        if not vals:
            return False

        hash, salt = vals

        if hash != scrypt.hash(password, salt):
            return False

        return True

    def create_project(self, email: str, name: str) -> str:
        """
        Create project.

        Parameters
        ----------
        email : str
            email of project admin.
        name : str
            project name.

        Returns
        -------
        str
            the project_id of the new project

        """
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        project_id = str(uuid.uuid4())

        c.execute('INSERT INTO projects VALUES(?,?)',
                  (project_id, name))
        c.execute('INSERT INTO admins VALUES(?,?)',
                  (project_id, email))
        c.execute('INSERT INTO members VALUES(?,?)',
                  (project_id, email))

        db.commit()
        db.close()

        return project_id

    def add_member(self, email: str, project_id: str) -> Tuple[bool, str]:
        """
        Attempt to add member to project.

        Parameters
        ----------
        email : str
            the member's id.
        project_id : str
            the project id.

        Returns
        -------
        Tuple[bool, str]
            True, '' on success.
            False, 'error message' on failure.

        """

        if not self.get_project_name(project_id)[0]:
            return False, 'Project does not exist.'

        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        c.execute('INSERT INTO members VALUES(?,?)',
                  (project_id, email))

        db.commit()
        db.close()

        return True, ''

    def delete_project(self, email: str, project_id: str) -> Tuple[bool, str]:
        """
        Attempt to delete project.

        Parameters
        ----------
        email : str
            email of user attempting to delete project.
        project_id : str
            project_id of project being deleted.

        Returns
        -------
        Tuple[bool, str]
            (True, '') upon successful deletion.
            (False, 'error_msg') otherwise.

        """
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        c.execute('SELECT email FROM admins WHERE project_id=?',
                  (project_id,))

        result = c.fetchone()
        print(result)

        if result is None:
            return False, 'Project does not exist.'

        if result[0] != email:
            return False, 'You do not own that project.'

        c.execute('DELETE FROM admins WHERE project_id=?',
                  (project_id,))
        c.execute('DELETE FROM members WHERE project_id=?',
                  (project_id,))
        c.execute('DELETE FROM projects WHERE project_id=?',
                  (project_id,))
        c.execute('DELETE FROM files WHERE project_id=?',
                  (project_id,))

        db.commit()
        db.close()

        return True, ''

    def get_projects(self, email: str) -> Tuple[str, ...]:
        """
        Get projects given an email.

        Parameters
        ----------
        email : str
            the email.

        Returns
        -------
        Tuple[str, ...]
            [project_id, ...]

        """
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        c.execute('SELECT project_id FROM members WHERE email=?',
                  (email,))

        projects = tuple(x[0] for x in c.fetchall())

        db.close()

        return projects

    def get_project_name(self, project_id: str) -> Tuple[bool, str]:
        """
        Get project name given id.

        Parameters
        ----------
        project_id : str
            the project id.

        Returns
        -------
        Tuple[bool, str]
            (True, 'project name') if project exists.
            (False, 'error_msg') otherwise

        """
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        c.execute('SELECT name FROM projects WHERE project_id=?',
                  (project_id,))

        name = c.fetchone()

        if name is None:
            return False, 'Project doesn\'t exist!'

        db.close()

        return True, name[0]

    def create_file(self, email: str, project_id: str,
                    name: str) -> Tuple[bool, str]:
        """
        Create file with given name in project.

        Parameters
        ----------
        email : str
            email of member creating file.
        project_id : str
            the project id.
        name : str
            the name of the file.

        Returns
        -------
        Tuple[bool, str]
            (True, '') on success.
            (False, 'error_msg') on failure.

        """
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        # Check if email is member of project
        c.execute('SELECT email FROM members WHERE project_id=? AND email=?',
                  (project_id, email))

        member = c.fetchone()

        if not member:
            return False, 'You don\'t have permission to do that.'

        # Check if file with name already exists in project
        c.execute('SELECT name FROM files WHERE project_id=? AND name=?',
                  (project_id, name))

        exists = c.fetchone()

        if exists:
            return False, 'File with that name already exists!'

        # Create file
        # TODO: Actually create the file in our filesystem
        file_id = str(uuid.uuid1())

        c.execute('INSERT INTO files VALUES(?,?,?)',
                  (file_id, project_id, name))

    def get_files(self, email: str, project_id: str) -> Tuple[str, ...]:
        """
        Get file_ids of files in project.

        Parameters
        ----------
        email : str
            the email of the user.
        project_id : str
            the project id.

        Returns
        -------
        Tuple[str, ...]
            [file_id, ...]

        """
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        c.execute('SELECT file_id FROM files WHERE project_id=?',
                  (project_id,))

        files = tuple(x[0] for x in c.fetchall())

        db.close()

        return files

    def get_file_name(self, file_id: str) -> Tuple[bool, str]:
        """
        Get name of file with given id.

        Parameters
        ----------
        file_id : str
            the id.

        Returns
        -------
        Tuple[bool, str]
            (True, 'file name') on success.
            (False, 'error_msg') on failure.

        """
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        c.execute('SELECT name FROM files WHERE file_id=?',
                  (file_id,))

        name = c.fetchone()

        if name is None:
            return False, 'That file doesn\'t exist!'

        db.close()

        return True, name[0]

    def is_teacher(self, email: str) -> bool:
        """
        Check if email is associated with a teacher.

        Parameters
        ----------
        email : str
            the email.

        Returns
        -------
        bool
            True if teacher.
            False otherwise.

        """

        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        c.execute('SELECT is_teacher FROM users WHERE email=?',
                  (email,))

        teacher = c.fetchone()

        if teacher is None:
            return False

        else:
            return bool(teacher[0])

    def is_admin(self, email: str, project_id: str) -> bool:
        """
        Check if email is admin for given project.

        Parameters
        ----------
        email : str
            the email.
        project_id : str
            the project.

        Returns
        -------
        bool
            True if so.
            False otherwise.

        """
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        c.execute('SELECT email FROM admins WHERE project_id=?',
                  (project_id,))

        admin = c.fetchone()

        if admin is None:
            return False

        return admin[0] == email

    def is_member(self, email: str, project_id: str) -> bool:
        """
        Check if email is project member.

        Parameters
        ----------
        email : str
            the email.
        project_id : str
            the project.

        Returns
        -------
        bool
            True if so.
            False otherwise.

        """
        db = sqlite3.connect(self.db_filename)
        c = db.cursor()

        c.execute('SELECT email FROM members WHERE email=? AND project_id=?',
                  (email, project_id))

        member = c.fetchone()

        if member is None:
            return False

        return member[0] == email
