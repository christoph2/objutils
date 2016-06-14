

class BaseClass(object):

  def __init__(self):
    pass
    
  def join(self, lines, lineSeparator = '\n'):
    """Make a printable chunk from a bunch of lines.
    :param lines:  Lines to be joined.
    :type lines: `iteratable` containing strings and the like.
    :param lineSeparator: As the name implies, a character or string used to separate lines.
    """
    if not hasattr(lines, '__iter__'):
      raise TypeError("'lines' must be iteratable.")
    return lineSeparator.join(lines)
    
##
## Tests.    
##
import unittest

class TestVisualBaseClass(unittest.TestCase):

  def testAnIterableIsNeededPass(self):
    bc = BaseClass()
    self.assertEqual(bc.join(("A", "B", "C")), "A\nB\nC")
    
  def testAnIteratableIsNeededFail(self):
    bc = BaseClass()
    self.assertRaises(TypeError, bc.join, 4711)


  def testLineSeparatorWorks(self):
    bc = BaseClass()
    self.assertEqual(bc.join(['X', 'Y', 'Z'], lineSeparator = '++'), "X++Y++Z")

def main():
  unittest.main()
  
  
if __name__ == '__main__':
  main()
