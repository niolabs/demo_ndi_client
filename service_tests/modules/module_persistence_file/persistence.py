import os
from enum import Enum

from nio.util.codec import load_pickle, load_json, save_pickle, save_json
from nio.util.logging import get_nio_logger


class Persistence(object):

    """ File based persistence module implementation

    This module implements the Persistence interface saving the information ]
    in either pickle or json format as specified when module is configured
    (default pickle)

    When saving an item within a collection, root_id is interpreted as an
    additional level, its filename will be then:
    [root_folder]/[root_id]/[collection]/id if root_id not is empty, otherwise
    [root_folder]/[collection]/id

    When item does not belong to a collection, its filename will be then:
    [root_folder]/[root_id]_[id] if root_id is not empty, otherwise:
    [root_folder]/[id]
    """

    class Format(Enum):
        pickle = 1
        json = 2

    _root_id = ''
    _root_folder = None
    _format = Format.pickle

    def __init__(self):
        """ Constructor for the Persistence module
        """
        self.logger = get_nio_logger("File-Persistence")

    @classmethod
    def configure(cls, context):
        """  Configures the persistence - this will be called before proxying.

        This method is called once in each process by the module implementation
        and is expected to set the global information for the persistence
        module. As a result, this method must be called before the
        implementation is proxied, since it makes use of cls which will always
        be the implementation.
        """
        cls._root_id = context.root_id
        cls._root_folder = context.root_folder
        try:
            os.makedirs(cls._root_folder)
        except OSError:
            # If the persistence target directory already exists, move on
            pass
        cls._format = context.format

    def load(self, id, collection=None, default=None):
        """ Load an item from the persistence store.

        Args:
            id (str): Specifies the identifier of the item to load.
            collection (str): if provided, it specifies the collection the item
                belongs to.
            default: the value to return if the item does not exist

        Returns:
            item: The item associated with given id
        """
        if collection is not None:
            filename = self._get_collection_item_filename(id, collection)
            return self._load_file(filename) or default
        else:
            filename = self._get_item_filename(id)
            return self._load_file(filename) or default

    def load_collection(self, collection, default=None):
        """ Load a collection from the persistence store.

        Args:
            collection (str): Specifies the collection to load
            default: the value to return if the collection does not exist

        Returns:
            items: The items associated with given collection
        """
        result = {}
        collection_folder = self._get_collection_folder(collection)
        extension = self._get_file_extension()
        if os.path.isdir(collection_folder):
            for filename in os.listdir(collection_folder):
                if os.path.splitext(filename)[1] != extension:
                    continue
                name = os.path.splitext(os.path.basename(filename))[0]
                result[name] = self._load_file(
                    os.path.join(collection_folder, filename))
        return result or default

    def save(self, item, id, collection=None):
        """ Save the item to the persistence store.

        Args:
            item: Item to save
            id (str): Specifies the identifier of the item to save.
            collection (str): if provided, it specifies the collection the item
                belongs to.
        """
        if collection is not None:
            filename = self._get_collection_item_filename(id, collection, True)
            self._save_file(item, filename)
        else:
            filename = self._get_item_filename(id)
            self._save_file(item, filename)

    def save_collection(self, items, collection):
        """ Save a collection to the persistence store.

        Args:
            items: Items to save
            collection (str): Specifies the collection to save
        """
        collection_folder = self._get_collection_folder(collection, True)
        for id, item in items.items():
            filename = \
                os.path.join(collection_folder,
                             "{}{}".format(id, self._get_file_extension()))
            self._save_file(item, filename)

    def remove(self, id, collection=None):
        """ Remove an item from the persistence store.

        Args:
            id (str): Specifies the identifier of the item to remove.
            collection (str): if provided, it specifies the collection the item
                belongs to.
        """
        if collection is not None:
            filename = self._get_collection_item_filename(id, collection)
            if os.path.isfile(filename):
                os.remove(filename)
        else:
            filename = self._get_item_filename(id)
            if os.path.isfile(filename):
                os.remove(filename)

    def remove_collection(self, collection):
        """ Remove a collection from the persistence store.

        Args:
            collection (str): Specifies the collection to remove
        """
        collection_folder = self._get_collection_folder(collection)
        if os.path.isdir(collection_folder):
            extension = self._get_file_extension()
            for filename in os.listdir(collection_folder):
                if os.path.splitext(filename)[1] != extension:
                    continue
                os.remove(os.path.join(collection_folder, filename))

    def _get_collection_folder(self, collection, ensure_dirs=False):
        """ Find out folder location for given collection

        Args:
            collection (str): collection name
            ensure_dirs (bool): if True, dirs are created if not exist

        Returns:
            Folder where files for given collection reside

        """
        # find out root folder interpreting _root_id as an optional additional
        # directory level
        root_folder = os.path.join(self._root_folder, self._root_id) \
            if self._root_id else self._root_folder
        # add collection name as an additional directory level
        collection_folder = os.path.join(root_folder, collection)
        if ensure_dirs:
            try:
                os.makedirs(collection_folder)
            except FileExistsError:  # pragma: no cover
                # No problem, the directory already exists
                pass

        return collection_folder

    def _get_collection_item_filename(self, id, collection, ensure_dirs=False):
        """ Provide filename for given id within a collection

        Args:
            id (str): item identifier
            collection (str): collection name
            ensure_dirs (bool): if True, dirs are created if not exist

        Returns:
            Filename for given item in the collection
        """
        collection_folder = \
            self._get_collection_folder(collection, ensure_dirs=ensure_dirs)
        return os.path.join(collection_folder,
                            "{}{}".format(id, self._get_file_extension()))

    def _get_item_filename(self, id):
        """ Provide filename for given id

        Args:
            id (str): item identifier

        Returns:
            Filename for given item
        """
        filename = "{}_{}".format(self._root_id, id) if self._root_id else id
        return os.path.join(self._root_folder,
                            "{}{}".format(filename, self._get_file_extension()))

    def _get_file_extension(self):
        if self._format == Persistence.Format.pickle.value:
            return ".dat"
        else:
            return ".cfg"

    def _load_file(self, filename):
        """ Load a file into a dictionary

        Args:
            filename (str): Absolute path to filename

        Returns:
            out (dict): Dictionary of loaded file. If there is an error, the
                message will be logged and an empty dict is returned.
        """
        try:
            if self._format == Persistence.Format.pickle.value:
                return load_pickle(filename)
            else:
                return load_json(filename)
        except Exception:  # pragma: no cover
            self.logger.exception(
                "Failed to parse {} file {}".format(self._format, filename))

    def _save_file(self, item, filename):
        """ Saves an item to disk

        If there is an error a message will be logged

        Args:
            item (dict): item information to save
            filename (str): Absolute path to filename
        """
        try:
            if self._format == Persistence.Format.pickle.value:
                save_pickle(filename, item)
            else:
                save_json(filename, item)
        except Exception:  # pragma: no cover
            self.logger.exception(
                "Failed to save {} file {}".format(self._format, filename))
