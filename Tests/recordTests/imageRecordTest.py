import unittest
import LotDataPackage.ExtractorsAndTables as eta
import LotDataPackage.Record as ld
import Browser as brwsr

class MyTestCase(unittest.TestCase):

    """

    We would like the indexing of our dataframe to represent the order that the images are shown to the user.
    This test only says anything if it is negative (TOSAN)
    

    """
    def test_correct_indexing(self):
        specific_closed_URL = "84993063"
        meta_data = eta.MetadataExtractor(specific_closed_URL,"","","")
        image_data_table = eta.ImagesTable("",brwsr.ImageApi.getImageGallery(specific_closed_URL))
        image_url_to_index = {
            "https://assets.catawiki.com/image/cw_ldp_l/plain/assets/catawiki/assets/2024/2/20/1/1/b/11ba8a9f-9636-4870-850e-25f5802d51ec.jpg": 0,
            "https://assets.catawiki.com/image/cw_large/plain/assets/catawiki/assets/2024/2/20/1/1/b/11ba8a9f-9636-4870-850e-25f5802d51ec.jpg": 0,
            "https://assets.catawiki.com/image/cw_ldp_l/plain/assets/catawiki/assets/2024/2/20/2/c/1/2c137ca1-59e7-4afd-9164-8ee33bb6949c.jpg": 1,
            "https://assets.catawiki.com/image/cw_large/plain/assets/catawiki/assets/2024/2/20/2/c/1/2c137ca1-59e7-4afd-9164-8ee33bb6949c.jpg": 1,
            "https://assets.catawiki.com/image/cw_ldp_l/plain/assets/catawiki/assets/2024/2/20/a/5/f/a5fd300e-00b8-4ede-a13e-bb5fbc8851a9.jpg": 2,
            "https://assets.catawiki.com/image/cw_large/plain/assets/catawiki/assets/2024/2/20/a/5/f/a5fd300e-00b8-4ede-a13e-bb5fbc8851a9.jpg": 2,
            "https://assets.catawiki.com/image/cw_ldp_l/plain/assets/catawiki/assets/2024/2/20/9/d/8/9d88b20f-7921-43e6-b1ed-1cfbec33482b.jpg": 3,
            "https://assets.catawiki.com/image/cw_large/plain/assets/catawiki/assets/2024/2/20/9/d/8/9d88b20f-7921-43e6-b1ed-1cfbec33482b.jpg": 3,
            "https://assets.catawiki.com/image/cw_ldp_l/plain/assets/catawiki/assets/2024/2/20/f/3/e/f3e9dafe-a956-41b3-b12d-0969f241f31d.jpg": 4,
            "https://assets.catawiki.com/image/cw_large/plain/assets/catawiki/assets/2024/2/20/f/3/e/f3e9dafe-a956-41b3-b12d-0969f241f31d.jpg": 4,
            "https://assets.catawiki.com/image/cw_ldp_l/plain/assets/catawiki/assets/2024/2/20/a/2/5/a2542c71-2f91-42bb-a3cf-9b2676329799.jpg": 5,
            "https://assets.catawiki.com/image/cw_large/plain/assets/catawiki/assets/2024/2/20/a/2/5/a2542c71-2f91-42bb-a3cf-9b2676329799.jpg": 5,
            "https://assets.catawiki.com/image/cw_ldp_l/plain/assets/catawiki/assets/2024/2/20/3/9/d/39d6f0e1-1e26-4e89-bb41-ca5a9dbe3469.jpg": 6,
            "https://assets.catawiki.com/image/cw_large/plain/assets/catawiki/assets/2024/2/20/3/9/d/39d6f0e1-1e26-4e89-bb41-ca5a9dbe3469.jpg": 6,
            "https://assets.catawiki.com/image/cw_ldp_l/plain/assets/catawiki/assets/2024/2/20/e/6/a/e6aebe02-03d1-40f7-b831-3b8475f2eb51.jpg": 7,
            "https://assets.catawiki.com/image/cw_large/plain/assets/catawiki/assets/2024/2/20/e/6/a/e6aebe02-03d1-40f7-b831-3b8475f2eb51.jpg": 7,
            "https://assets.catawiki.com/image/cw_ldp_l/plain/assets/catawiki/assets/2024/2/20/8/c/d/8cdb5c8a-cc01-4157-8737-65891dcb0f62.jpg": 8,
            "https://assets.catawiki.com/image/cw_large/plain/assets/catawiki/assets/2024/2/20/8/c/d/8cdb5c8a-cc01-4157-8737-65891dcb0f62.jpg": 8,
            "https://assets.catawiki.com/image/cw_ldp_l/plain/assets/catawiki/assets/2024/2/20/5/0/3/50333084-fdde-4109-900b-1523f9462687.jpg": 9,
            "https://assets.catawiki.com/image/cw_large/plain/assets/catawiki/assets/2024/2/20/5/0/3/50333084-fdde-4109-900b-1523f9462687.jpg": 9,
            "https://assets.catawiki.com/image/cw_ldp_l/plain/assets/catawiki/assets/2024/2/20/f/d/3/fd3b6830-c8a8-48f1-b11d-aa7badda114e.jpg": 10,
            "https://assets.catawiki.com/image/cw_large/plain/assets/catawiki/assets/2024/2/20/f/d/3/fd3b6830-c8a8-48f1-b11d-aa7badda114e.jpg": 10
        }
        image_record = ld.ImageRecord({"meta_data":meta_data,"image_data":image_data_table})
        image_record_df = image_record.getRecordForDatabaseCopy()

        for real_url, real_idx in image_url_to_index.items():
            filtered_df = image_record_df[image_record_df["url"] == real_url]
            self.assertTrue(not filtered_df.empty, f"URL {real_url} not found in DataFrame")
            self.assertEqual(filtered_df.iloc[0]["image_idx"], real_idx, f"Index mismatch for URL {real_url}")


if __name__ == '__main__':
    unittest.main()
