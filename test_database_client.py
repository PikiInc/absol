import unittest
from database_client import PUBLIC_IP
from pymongo import MongoClient


class TestMongoClient(unittest.TestCase):

    def setUp(self):
        self.mongo_client = MongoClient(PUBLIC_IP, 27017)
        self.test_db = self.mongo_client.test_database
        self.test_collection = self.test_db.test_collection
        self.test_collection.remove()

    def tearDown(self):
        self.test_collection.drop()
        self.mongo_client.drop_database(self.test_db)
        self.mongo_client.close()

    def test_mongo_client(self):
        self.assertEqual(0, self.test_collection.count())
        sample_doc = {
            'name': 'test1',
            'desc': 'This is a test document.'
        }
        self.test_collection.insert(sample_doc)
        self.assertEqual(1, self.test_collection.count())
        self.assertEqual('test1', self.test_collection.find_one().get('name'))
        self.test_collection.remove()
        self.assertEqual(0, self.test_collection.count())

if __name__ == '__main__':
    unittest.main()
