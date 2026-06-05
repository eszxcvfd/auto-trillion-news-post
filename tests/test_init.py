import os
import shutil
import tempfile
import unittest
from main import init_project

class TestInitProject(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        # Restore CWD and remove the temporary directory
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    def test_init_creates_files_and_directories(self):
        # Call the init function
        init_project()

        # Check files
        expected_files = [".env.example", "config.yaml", "keywords.txt"]
        for filename in expected_files:
            self.assertTrue(os.path.exists(filename), f"{filename} should be created")
            # Verify file has content
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertTrue(len(content) > 0, f"{filename} should not be empty")

        # Check directories
        expected_dirs = [
            "output",
            "output/posts",
            "output/Ảnh Trillion $ news",
            "output/logs"
        ]
        for dirname in expected_dirs:
            self.assertTrue(os.path.exists(dirname), f"Directory {dirname} should be created")
            self.assertTrue(os.path.isdir(dirname), f"{dirname} should be a directory")

    def test_init_does_not_overwrite_existing_files(self):
        # Create a file with custom content beforehand
        custom_content = "custom content here"
        with open("config.yaml", "w", encoding="utf-8") as f:
            f.write(custom_content)

        # Call the init function
        init_project()

        # Verify config.yaml was not overwritten
        with open("config.yaml", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertEqual(content, custom_content, "config.yaml should not be overwritten")

if __name__ == "__main__":
    unittest.main()
