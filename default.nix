{ lib, python3Packages }:

python3Packages.buildPythonPackage {
  pname = "paperless-generic-file-parser";
  version = "0.1.0";
  pyproject = true;
  src = lib.cleanSource ./.;

  build-system = [
    python3Packages.setuptools
  ];

  dependencies = [
    python3Packages.pillow
  ];

  pythonImportsCheck = [
    "paperless_generic_file_parser"
  ];

  meta = {
    description = "Generic file archiver parser plugin for Paperless-ngx";
    homepage = "https://github.com/paperless-ngx/paperless-ngx";
    platforms = lib.platforms.linux;
  };
}
