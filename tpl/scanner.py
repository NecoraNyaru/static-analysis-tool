import os
import logging
import json
import sys

file_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(file_dir, ".."))
sys.path.insert(0, os.getcwd())
import argparse

from tpl.utils.utils import read_txt, save_js
from tpl.extractors.conan_extractor import ConanExtractor
from tpl.extractors.control_extractor import ControlExtractor
from tpl.extractors.cmake_extractor import CmakeExtractor
from tpl.extractors.autoconf_extractor import AutoconfExtractor
from tpl.extractors.submodule_extractor import SubmodExtractor
from tpl.extractors.vcpkg_extractor import VcpkgExtractor
from tpl.extractors.pkg_extractor import PkgExtractor
from tpl.extractors.meson_extractor import MesonExtractor
from tpl.extractors.clib_extractor import ClibExtractor
from tpl.extractors.bazel_extractor import BazelExtractor
from tpl.extractors.ms_extractor import MsExtractor
from tpl.extractors.xmake_extractor import XmakeExtractor
from tpl.extractors.make_extractor import MakeExtractor

# from tpl.extractors.buckaroo_extractor import BuckarooExtractor
from tpl.extractors.dds_extractor import DdsExtractor

# from tpl.extractors.buck_extractor import BuckExtractor
from tpl.extractors.build2_extractor import Build2Extractor

parser = argparse.ArgumentParser()
parser.add_argument("-d", type=str, default="", help="set directory to scan")
parser.add_argument("-t", type=str, default="results.json", help="save results to file")

CONF_FILES = ["configure", "configure.in", "configure.ac"]
logging.basicConfig()
logger = logging.getLogger(__name__)


class scanner(object):
    def __init__(self, dir_target) -> None:
        self.target = dir_target
        self.extractors = []
        self.scan()

    def scan(self):
        for root, dirs, filenames in os.walk(self.target):
            for filename in filenames:
                extractor = None
                filename_lower = filename.lower()
                ## TODO: readme module
                # if filename_lower.startswith('readme'):
                #     extractor = ReadmeExtractor
                #     arg = os.path.join(root, filename)
                if filename_lower == "control" or filename_lower.endswith(".dsc"):
                    extractor = ControlExtractor
                    arg = os.path.join(root, filename)
                elif filename == "CMakeLists.txt" or filename.endswith(".cmake"):
                    extractor = CmakeExtractor
                    arg = os.path.join(root, filename)
                elif filename_lower in CONF_FILES:
                    extractor = AutoconfExtractor
                    arg = os.path.join(root, filename)
                elif filename == ".gitmodules":
                    extractor = SubmodExtractor
                    arg = root
                elif filename == "vcpkg.json":
                    extractor = VcpkgExtractor
                    arg = os.path.join(root, filename)
                elif filename in ["conanfile.txt", "conaninfo.txt", "conanfile.py"]:
                    extractor = ConanExtractor
                    arg = os.path.join(root, filename)
                elif filename.endswith(".pc"):
                    extractor = PkgExtractor
                    arg = os.path.join(root, filename)
                elif filename == "meson.build":
                    extractor = MesonExtractor
                    arg = os.path.join(root, filename)
                elif filename in ["package.json", "clib.json"]:
                    extractor = ClibExtractor
                    arg = os.path.join(root, filename)
                elif filename == "package.json5":
                    extractor = DdsExtractor
                    arg = os.path.join(root, filename)
                elif filename in ["bazel.build", "BUILD"]:
                    extractor = BazelExtractor
                    arg = os.path.join(root, filename)
                elif filename.endswith((".vcxproj", ".vbproj", ".props")):
                    extractor = MsExtractor
                    arg = os.path.join(root, filename)
                elif filename == "xmake.lua":
                    extractor = XmakeExtractor
                    arg = os.path.join(root, filename)
                ## elif filename in ['buckaroo.toml', 'buckaroo.lock.toml', '.buckconfig']:
                # elif filename in 'buckaroo.toml':
                #     extractor = BuckarooExtractor
                #     arg = os.path.join(root, filename)
                # elif filename == 'BUCK':
                #     extractor = BuckExtractor
                #     arg = os.path.join(root, filename)
                elif filename.lower().startswith("makefile"):
                    extractor = MakeExtractor
                    arg = os.path.join(root, filename)
                elif filename.lower() == "manifest":
                    file_path = os.path.join(root, filename)
                    context = read_txt(file_path)
                    if "build2" not in context:
                        continue
                    extractor = Build2Extractor
                    arg = file_path

                if extractor is None:
                    continue
                try:
                    extractor = extractor(arg)
                    extractor.run_extractor()
                    self.extractors.append(extractor.to_dict())
                except Exception as e:
                    logger.error(e)

    def to_dict(self):
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))


def main():
    args = parser.parse_args()
    target = args.d
    save_file = args.t
    scanner_obj = scanner(target)
    res = scanner_obj.to_dict()
    save_js(res, save_file)


if __name__ == "__main__":
    main()
    # target = 'data/targets/projects/wireshark'
    # target = 'data/data_debian/salsa_repo_src/a11y-team@@at-spi2-atk'
    # target = 'tests/test_data'
    # res = test_scanner(target)
    # print(res)
