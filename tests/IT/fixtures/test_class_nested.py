class TestOuter(object):

    class TestInner(object):

        @classmethod
        def setup_class(cls):
            pass

        @classmethod
        def teardown_class(cls):
            pass

        def setup_method(self, method):
            pass

        def teardown_method(self, method):
            pass

        def test(self):
            assert 2 + 2 == 4

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass

    def test(self):
        assert 2 + 2 == 4
