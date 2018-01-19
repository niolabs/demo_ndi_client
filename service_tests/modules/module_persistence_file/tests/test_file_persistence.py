import os
import shutil

from nio.testing import NIOTestCase
from nio.modules.persistence import Persistence
from nio.modules.context import ModuleContext

from ..persistence import Persistence as PersistenceModule
from ..module import FilePersistenceModule


class TestFilePersistence(NIOTestCase):

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
            context.format = PersistenceModule.Format.pickle.value
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

    def test_item(self):
        """ Asserts persistence at the item level """

        persist = Persistence()
        persist.save('item_val', 'item_id')

        # Make sure we get the saved value
        self.assertEqual(
            persist.load('item_id', default='not found'),
            'item_val')

        # Make sure we get a default value if one hasn't been saved
        self.assertEqual(
            persist.load('invalid_id', default='default_val'),
            'default_val')

        # Remove item
        persist.remove('item_id')

        # not it behaves as it never existed
        self.assertEqual(
            persist.load('item_id', default='default_val'),
            'default_val')

    def test_collection_item(self):
        """ Asserts item persistence within a collection """

        persist = Persistence()
        persist.save('collection_item_val', 'item_id',
                     collection='item_collection')
        persist.save('item_val', 'item_id')

        # Make sure we get the correct value depending on collection argument
        self.assertEqual(persist.load('item_id', collection='item_collection'),
                         'collection_item_val')
        self.assertEqual(persist.load('item_id'), 'item_val')

        # Remove item
        persist.remove('item_id', collection='item_collection')
        self.assertEqual(persist.load('item_id', collection='item_collection',
                                      default='default_val'),
                         'default_val')

    def test_collection(self):
        """ Asserts collection persistence """

        items = {"item1": "item1_val", "item2": "item2_val"}

        persist = Persistence()
        persist.save_collection(items, 'item_id')

        # load it back and assert results
        self.assertDictEqual(persist.load_collection('item_id'), items)

        # Remove item
        persist.remove_collection('item_id')
        self.assertEqual(persist.load_collection('item_id',
                                                 default='default_val'),
                         'default_val')

    def test_save_item_in_collection(self):
        persistence = Persistence()
        item = {
            "field1": "value1"
        }
        collection = "col1"
        id = "one"
        expected_file_name = os.path.join(self.cfg_dir, collection,
                                          "{}.dat".format(id))
        self.assertFalse(os.path.isfile(expected_file_name))
        persistence.save(item, id, collection=collection)
        self.assertTrue(os.path.isfile(expected_file_name))

        items = persistence.load_collection("col1")
        self.assertEqual(len(items), 1)
