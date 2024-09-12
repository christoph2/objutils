import unittest


class DummyReader:
    pass


class DummyWriter:
    pass


class TestRegistry(unittest.TestCase):
    CODECS = ("A", "B", "C", "X", "Y", "Z")

    """
    def tearDown(self):
        self.clearRegistry()

    def testRegistryShallBeEmpty(self):
        self.assertEqual(objutils.registry.registry(), {})

    def registerSomeCodecs(self):
        for cdc in self.CODECS:
            objutils.registry.register(cdc, DummyReader, DummyWriter)

    def clearRegistry(self):
        objutils.registry.codecs = {}

    def testRegistration(self):
        self.registerSomeCodecs()
        self.assertEqual(sorted(objutils.registry.getFormats()), ['A', 'B', 'C', 'X', 'Y', 'Z'])

    def testGetCodec(self):
        self.registerSomeCodecs()
        self.assertIsInstance(objutils.registry.getCodec('C'), objutils.registry.Codec)

    def testCodecNotFound(self):
        self.registerSomeCodecs()
        with self.assertRaises(objutils.registry.CodecDoesNotExistError):
            cdc =  objutils.registry.getCodec('Foo')

    def testCodecAlreadyExists(self):
        self.registerSomeCodecs()
        with self.assertRaises(objutils.registry.CodecAlreadyExistError):
            objutils.registry.register('X', DummyReader, DummyWriter)
    """


if __name__ == "__main__":
    unittest.main()
