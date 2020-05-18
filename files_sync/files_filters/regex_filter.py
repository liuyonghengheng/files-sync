import re
from watchdog.utils import has_attribute, unicode_paths
from files_sync.files_filters.files_filter import FilesFilter


class RegexFilter(FilesFilter):
    def __init__(self, logger, regexes=[r".*"], ignore_regexes=[], ignore_directories=False, case_sensitive=False):
        if case_sensitive:
            self._regexes = [re.compile(r) for r in regexes]
            self._ignore_regexes = [re.compile(r) for r in ignore_regexes]
        else:
            self._regexes = [re.compile(r, re.I) for r in regexes]
            self._ignore_regexes = [re.compile(r, re.I) for r in ignore_regexes]
        self._ignore_directories = ignore_directories
        self._case_sensitive = case_sensitive
        self.logger = logger
        self.logger.info("matching_regexes:{a}".format(a=self._ignore_regexes))
        self.logger.info("ignore_regexes:{a}".format(a=self._ignore_regexes))

    def event_filter(self, event):
        if self._ignore_directories and event.is_directory:
            return False

        paths = []
        if has_attribute(event, 'dest_path'):
            paths.append(unicode_paths.decode(event.dest_path))
        if event.src_path:
            paths.append(unicode_paths.decode(event.src_path))

        if any(r.match(p) for r in self._ignore_regexes for p in paths):
            self.logger.info("ignore regexes match:+ {paths}".format(paths=paths))
            return False

        if any(r.match(p) for r in self._regexes for p in paths):
            return True

        return True

    def filter_paths(self, paths):
        retain_paths = [p for p in paths if not self.is_ignore_path(p) and self.is_retain_path(p)]
        return retain_paths

    def is_ignore_path(self, path):
        for r in self._ignore_regexes:
            if r.match(path):
                return True
        return False

    def is_retain_path(self, path):
        for r in self._regexes:
            if r.match(path):
                return True
        return False


def get_filter(conf, logger):
    return RegexFilter(logger,
                       regexes=[conf.match_files_regexp],
                       ignore_regexes=[conf.ignore_files_regexp],
                       ignore_directories=False,
                       case_sensitive=True)
