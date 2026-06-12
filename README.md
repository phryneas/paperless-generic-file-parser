# Paperless generic file parser

This plugin archives selected files in Paperless-ngx as original files.
It does not parse, render, sanitize, execute, or inspect file contents beyond
filesystem metadata such as filename, suffix, and size.

## What it does

- Accepts only conservative MIME types by default:
  - `text/html`
  - `application/xhtml+xml`
- Preserves the original uploaded file unchanged.
- Stores minimal searchable text:
  - filename
  - MIME type
  - extension
  - byte size
  - a static marker string
- Generates a generic thumbnail.
- Generates a synthetic one-page PDF preview so Paperless does not
  inline-render active content like HTML in the browser.

## Why the synthetic PDF exists

This is the important safety tradeoff.

Current Paperless serves non-archived originals from its preview endpoint with
`Content-Disposition: inline`, and the frontend renders unknown formats with an
`<object>` element. For `text/html`, that can cause the browser to render the
original HTML directly.

So for a production-safe "archive/download only" workflow, this plugin defaults
to creating an inert placeholder PDF preview while still preserving the
original file unchanged for download.

This plugin always uses the safe rendition path:

- `requires_pdf_rendition = True`
- `can_produce_archive = True`
- preview uses a synthetic PDF, not the original active file

## Conservative MIME configuration

- `text/html`
- `application/xhtml+xml`
- `application/octet-stream` is intentionally not supported

## NixOS integration

Add this plugin package to the Paperless Python environment from GitHub:

```nix
{ pkgs, lib, ... }:
{
  services.paperless = {
    enable = true;
    package =
      let
        paperlessGenericFileParser =
          pkgs.paperless-ngx.python.pkgs.callPackage
            (pkgs.fetchFromGitHub {
              owner = "phryneas";
              repo = "paperless-generic-file-parser";
              rev = "REPLACE_WITH_COMMIT_OR_TAG";
              hash = "sha256-REPLACE_WITH_NIX_HASH";
            })
            { };

        addGenericFileParser = pkg:
          pkg.overridePythonAttrs (old: {
            dependencies = (old.dependencies or [ ]) ++ [ paperlessGenericFileParser ];
            propagatedBuildInputs =
              (old.propagatedBuildInputs or [ ]) ++ [ paperlessGenericFileParser ];
          });

        pkg = addGenericFileParser pkgs.paperless-ngx;
      in
      pkg // {
        override = args: addGenericFileParser (pkgs.paperless-ngx.override args);
      };
  };
}
```

## Test plan

Use a tiny file like this:

```html
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>paperless generic parser test</title>
  </head>
  <body>
    <script>
      console.log("do not execute in preview");
    </script>
  </body>
</html>
```

Recommended validation flow:

1. Save that file outside the consume directory first, for example `/tmp/generic-test.html`.
2. Record its checksum:
   - `sha256sum /tmp/generic-test.html`
3. Copy it into the Paperless consume directory.
4. Wait for import or watch:
   - `journalctl -u paperless-consumer -f`
5. In the UI, confirm:
   - the document imports successfully
   - the thumbnail is synthetic
   - the content field contains only metadata text
   - the preview is a synthetic PDF page, not live HTML
6. Download the original from Paperless.
7. Compare checksums:
   - `sha256sum downloaded-file.html`
   - it should match the original checksum exactly

## Limitations and warnings

- This is for archive and download, not for interactive use inside Paperless.
- The original HTML app will not run inside the safe preview path.
- The preview PDF is synthetic and intentionally does not contain the original document content.
- Search quality is minimal by design.
- MIME detection still matters: if libmagic identifies a file as something not in
  `SUPPORTED_MIME_TYPES`, this parser will not claim it.
- Downloading the original later still gives you the raw file. If a user opens
  that original in a browser or another application, that application may still
  execute or interpret it. This plugin only avoids content handling during
  ingestion and safe preview.
- Do not register `application/octet-stream` unless you really want Paperless to
  ingest a much broader class of arbitrary files.
