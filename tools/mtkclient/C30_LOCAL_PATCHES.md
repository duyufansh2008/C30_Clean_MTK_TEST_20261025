# C30 local patches

Upstream input: `7cb40e727727dfe3faa065eefb29b16ed29bbdf1`.
`C30_SOURCE_MANIFEST.json` records the original upstream inputs; it is intentionally not rewritten to pretend these patches are upstream. Root `SHA256SUMS.json` covers the current patched files.

- `mtkclient/Library/DA/mtk_da_handler.py`: propagate GPT/read/write/erase errors; preflight all input filenames; stop at the first failed partition. When the C30 runner supplies `C30_PACKAGE_ROOT`, keep DA state in `backup/` and run the package's live device/GPT guard before dispatching a command.
- `mtkclient/Library/mtk_main.py`: report connection/configuration failure as an error. For the C30 runner, restrict commands and verify the complete package before connecting for writes/erases.

The environment marker is set internally by `tools/run_mtk.py`. It is an integration switch, not an authentication boundary. Running a separate raw upstream tool is outside the package's safety guarantees. Error propagation remains active without the marker.

Tests: `python -m unittest discover -s tests -v`. Hardware/DA negotiation is not covered by synthetic tests.
