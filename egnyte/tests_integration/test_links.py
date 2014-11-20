from egnyte import const, exc

from egnyte.tests_integration.config import TestCase


class TestLinks(TestCase):
    def test_folder_link_duplicates(self):
        folder = self.root_folder.folder("link_duplicates").create()
        links = folder.link(const.LINK_ACCESSIBILITY_ANYONE, recipients=['test1@example.com', 'test2@example.com'],
                            send_email=False)
        link_one = links[0]
        link_two = links[1]
        self.assertEqual(link_one.path, link_two.path, "Both links should point to the same file")
        self.assertEqual(("test1@example.com",), tuple(link_one.recipients), "Link one should be for first email")
        self.assertNotEqual(link_one.id, link_two.id, "Links should have different ids")

        link_one.delete()
        link_two.check()  # link two should still exist
        self.assertRaises(exc.NotFound, link_one.check)  # link one should no longer exist
        link_two.delete()