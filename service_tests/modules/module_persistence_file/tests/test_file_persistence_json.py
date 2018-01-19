import os
import shutil

from nio.testing import NIOTestCase
from nio.modules.persistence import Persistence
from nio.modules.context import ModuleContext

from ..persistence import Persistence as PersistenceModule
from ..module import FilePersistenceModule


class TestJsonFilePersistence(NIOTestCase):

    cfg_dir = "{}/{}/".format(os.path.dirname(__file__), "persist_test")

    def setUp(self):
        try:
            os.mkdir(self.cfg_dir)
        except FileExistsError:  # pragma: no cover
            # No problem, the directory already exists
            pass

        # set up here after doing all of the file stuff
        # this will proxy the modules and set them up
        super().setUp()
        # Make sure the module has the proper class variables
        self.assertIsNotNone(Persistence._root_folder)
        # Make sure root_id is empty
        self.assertEqual(Persistence._root_id, '')

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.cfg_dir)

    def get_context(self, module_name, module):
        if module_name == "persistence":
            context = ModuleContext()
            context.root_folder = self.cfg_dir
            context.root_id = ''
            context.format = PersistenceModule.Format.json.value
            return context
        else:
            return super().get_context(module_name, module)

    def get_module(self, module_name):
        """ Override to use the file persistence """
        if module_name == "persistence":
            return FilePersistenceModule()
        else:
            return super().get_module(module_name)

    def get_test_modules(self):
        return super().get_test_modules() | {'persistence'}

    def test_save_json_item_in_collection(self):
        persistence = Persistence()
        item = {
            "field1": "value1"
        }
        collection = "col1"
        id = "one"
        expected_file_name = os.path.join(self.cfg_dir, collection,
                                          "{}.cfg".format(id))
        self.assertFalse(os.path.isfile(expected_file_name))
        persistence.save(item, id, collection=collection)
        self.assertTrue(os.path.isfile(expected_file_name))

        items = persistence.load_collection("col1")
        self.assertEqual(len(items), 1)
