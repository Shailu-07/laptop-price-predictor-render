import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class AppSmokeTest(unittest.TestCase):
    def test_load_and_predict(self):
        app = AppTest.from_file(str(Path(__file__).with_name('app.py'))).run(timeout=60)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.slider[0].label, 'Screen size (in inches)')
        app.button[0].click().run(timeout=60)
        self.assertEqual(len(app.exception), 0)
        self.assertGreater(int(app.title[-1].value.rsplit(' ', 1)[-1]), 0)
        app.slider[0].set_value(18.0)
        app.selectbox[4].select('Yes')
        app.button[0].click().run(timeout=60)
        self.assertEqual(len(app.exception), 0)
        self.assertGreater(int(app.title[-1].value.rsplit(' ', 1)[-1]), 0)


if __name__ == '__main__':
    unittest.main()
