# Imports

import commands
import os
from config import Config, Section
from packaging import PackageConfig
from ..constants import ENVIRONMENTS

# Exports

__all__ = (
    "autoload_project",
    "get_projects",
    "get_project_clients",
    "get_project_statuses",
    "get_project_types",
    "Project",
)

# Functions


def autoload_project(name, include_disk=False, path="./"):
    """Attempt to automatically load the project configuration based on the name and path.

    :param name: The project name, or possible name.
    :type name: str

    :param include_disk: Whether to calculate disk space.
    :type include_disk: bool

    :param path: The base path to search.
    :type path: str

    :rtype: Project
    :returns: A ``Project`` instance or ``None`` if the project could not be found.

    """
    name = name.lower()
    names = (
        name,
        name.replace(".", "_"),
        name.replace(" ", "-"),
        name.replace(" ", "_"),
    )

    for name in names:
        root_path = os.path.join(path, name)
        if os.path.exists(root_path):
            project = Project(name, root_path)
            project.load(include_disk=include_disk)
            return project

    return None


def get_projects(path, criteria=None, include_disk=False, show_all=False):
    """Get a list of projects.

    :param path: Path to where projects are stored.
    :type path: str

    :param criteria: Criteria used to filter the list, if any.
    :type criteria: dict

    :param include_disk: Whether to calculate disk space used by the project.
    :type include_disk: bool

    :param show_all: By default, projects without a ``project.ini`` file are omitted. Set this to ``True`` to show all
                     projects.

    :type show_all: bool

    :rtype: list

    """
    names = list()
    projects = list()

    entries = os.listdir(path)

    for project_name in entries:

        # Get the project root path.
        project_root = os.path.join(path, project_name)

        # Projects are always stored as sub directories of path.
        if not os.path.isdir(project_root):
            continue

        # Skip projects we've already found.
        if project_name in names:
            continue

        # Load the project.
        project = Project(project_name, project_root)
        project.load(include_disk=include_disk)
        # print(project)

        # We skip the display of the project if a project config does not exist and show_all is False.
        if not project.config_exists and not show_all:
            continue

        # Filter based on criteria, which should be a dict.
        if criteria:
            for field, search in criteria.items():
                value = getattr(project, field)
                if search == value:
                    projects.append(project)
        else:
            projects.append(project)

    return projects


def get_project_clients(path):
    clients = list()

    projects = get_projects(path)
    for p in projects:
        if p.org not in clients:
            clients.append(p.org)

    return sorted(clients)


def get_project_statuses(path):
    statuses = list()

    projects = get_projects(path)
    for p in projects:
        if p.status not in statuses:
            statuses.append(p.status)

    return sorted(statuses)


def get_project_types(path):
    types = list()

    projects = get_projects(path)
    for p in projects:
        if p.type not in types:
            types.append(p.type)

    return sorted(types)


# Classes


class Project(Config):

    def __init__(self, name, root, debug=False):
        """Initialize a project object.

        :param name: The name of the project.
        :type name: str

        :param root: The path to the project.
        :type root: str

        :param debug: Enable debug mode. Only useful in development.
        :type debug: bool

        """
        self.config_exists = None
        self.description = None
        self.disk = "TBD"
        self.is_dirty = None
        self.is_loaded = False
        self.name = name
        self.org = "Unknown"
        self.root = root
        self.scm = None
        self.status = "unknown"
        self.tags = list()
        self.title = None
        self.type = "project"
        self.version = "0.1.0-d"
        self._requirements = list()

        config_path = os.path.join(root, "project.ini")
        if os.path.exists(config_path):
            self.config_exists = True
        else:
            self.config_exists = False

        super(Project, self).__init__(config_path, debug=debug)

    def __str__(self):
        return self.title or self.name or "Untitled Project"

    def get_context(self):
        """Get project data as a dictionary.

        :rtype: dict

        """
        d = {
            'config_exists': self.config_exists,
            'description': self.description,
            'disk': self.disk,
            'name': self.name,
            'org': self.org,
            'root': self.root,
            'scm': self.scm,
            'status': self.status,
            'title': self.title,
            'type': self.type,
            'version': self.version,
        }

        for section_name in self._sections:
            d[section_name] = getattr(self, section_name)

        return d

    def get_dependencies(self):
        """Get project dependencies from a ``packages.ini`` file.

        :rtype list
        :returns: A list of ``(env, packages)``.

        """
        # TODO: Add public documentation for project dependencies.
        locations = (
            os.path.join("deploy", "requirements", "packages.ini"),
            os.path.join("requirements/packages.ini"),
            os.path.join("requirements.ini"),
        )

        a = list()
        for i in locations:
            if self._file_exists(i):
                path = os.path.join(self.root, i)

                config = PackageConfig(path, debug=self.debug)
                config.load()

                for env in ENVIRONMENTS:
                    a.append((env, config.get_packages(env=env)))

        return a

    def get_requirements(self, env=None):
        locations = (
            os.path.join("deploy", "requirements", "packages.ini"),
            os.path.join("requirements/packages.ini"),
            os.path.join("requirements.ini"),
        )

        for i in locations:
            if self._file_exists(i):
                path = os.path.join(self.root, i)

                config = PackageConfig(path, debug=self.debug)
                if config.load():
                    return config.get_packages(env=env)


        return None

    def load(self, include_disk=False):
        """Load the project.

        :param include_disk: Whether to calculate disk usage.
        :type include_disk: bool

        :rtype: bool
        :returns: Returns ``True`` if the project was found and loaded successful. This also sets ``is_loaded`` to
                  ``True``.

        """
        # We can't do anything if the project root doesn't exist.
        if not os.path.exists(self.root):
            self.is_loaded = False
            return False

        # Let the underlying Config do it's thing.
        super(Project, self).load()

        # Make sure we always have title.
        if not self.title:
            self.title = self.name

        # Get meta data.
        self.org = self._get_org()
        self.scm = self._get_scm().strip()
        self.version = self._get_version()

        # Calculate disk space.
        if include_disk:
            self.disk = self._get_disk()

        return self.is_loaded

    def to_markdown(self):
        """Output the project as Markdown.

        :rtype: str

        """
        # TODO: Create a TEMPLATE for markdown export and make this configurable from a switch.

        # Build the top/main section of the output.
        a = list()
        a.append("# %s" % self.title)
        a.append("")

        a.append("**Version**: %s  " % self.version)
        a.append("**Status**: %s  " % self.status)
        a.append("**Type**: %s  " % self.type)
        a.append("**Disk Usage**: %s  " % self._get_disk())
        a.append("**Source Code Management**: %s  " % self._get_scm())

        if self.tags:
            a.append("**Tags**: %s" % ",".join(self.tags))

        a.append("")

        # Add the description.
        if self.description:
            a.append(self.description)
            a.append("")

        # Add each section to the output.
        context = self.get_context()
        for key, value in context.items():
            if isinstance(value, Section):
                a.append(value.to_markdown())
            else:
                pass

        # List the dependencies.
        deps = self.get_dependencies()
        if deps:
            a.append("## Dependencies")
            a.append("")

            for env, packages in deps:

                if len(packages) == 0:
                    continue

                a.append("### %s" % env)
                a.append("")

                for p in packages:
                    a.append(p.to_markdown())

        # Include the project tree.
        a.append("## Tree")
        a.append("")
        status, output = commands.getstatusoutput("tree %s" % self.root)
        for line in output.split("\n"):
            a.append("    %s" % line)

        a.append("")

        return "\n".join(a)

    def _file_exists(self, name):
        if not self.root:
            raise ValueError("project root must be defined")

        path = os.path.join(self.root, name)
        return os.path.exists(path)

    def _get_disk(self):
        cmd = "du -hs %s | awk -F ' ' '{print $1}'" % self.root
        (status, output) = commands.getstatusoutput(cmd)
        return output.strip()

    def _get_org(self):
        obj = getattr(self, "client", None)
        if obj:
            try:
                return obj.code
            except AttributeError:
                return "Unidentified"

        obj = getattr(self, "business", None)
        if obj:
            try:
                return obj.code
            except AttributeError:
                return "Internal"

        return "Unknown"

    def _get_path(self, name):
        return os.path.join(self.root, name)

    def _get_scm(self):
        """Determine the SCM in use and get the current state."""
        if self._file_exists(".git"):
            # See http://stackoverflow.com/a/5737794/241720
            cmd = '(cd %s && test -z "$(git status --porcelain)")' % self.root
            (status, output) = commands.getstatusoutput(cmd)
            if status >= 1:
                self.is_dirty = True
            else:
                self.is_dirty = False

            return "git"
        elif self._file_exists(".hg"):
            # TODO: Determine if hg repo is dirty.
            return "hg"
        elif self._file_exists("trunk"):
            # TODO: Determine if svn repo is dirty.
            return "svn"
        else:
            return "None"

    def _get_version(self):
        if self._file_exists("VERSION.txt"):
            with open(self._get_path("VERSION.txt"), "rb") as f:
                v = f.read().strip()
                f.close()
                return v
        else:
            return "0.1.0-d"

    def _load_section(self, name, values):
        """Overridden to add project section values to the current instance."""
        if name == "project":
            for key in values.keys():
                setattr(self, key, values[key])
        else:
            super(Project, self)._load_section(name, values)