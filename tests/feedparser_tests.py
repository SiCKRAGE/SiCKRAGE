import unittest
import test_lib as test

if __name__ == '__main__':
    import sys, os.path
    sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
    sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickbeard.rssfeeds import RSSFeeds

class FeedParserTests(unittest.TestCase):
    def test_can_parse_feeds(self):
        RSSFeeds().clearCache()
        result = RSSFeeds().getFeed('http://showrss.info/feeds/978.rss')
        self.assertTrue('feed' in result)
        self.assertTrue('subtitle' in result.feed)
        self.assertTrue('links' in result.feed)

if __name__ == "__main__":
    print "=================="
    print "STARTING - FEEDPARSER TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(FeedParserTests)
    testresults = unittest.TextTestRunner(verbosity=2).run(suite)

    # Return 0 if successful, 1 if there was a failure
    sys.exit(not testresults.wasSuccessful())
