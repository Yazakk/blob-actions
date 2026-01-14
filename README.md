# blob-actions

Reusable helpers for creating Blob Storage folder skeletons and uploading
matching local directory trees. The API is intentionally generic so it can be
used across projects with different structures.

## Features

- Create container and prefix "folders" on demand.
- Build nested prefix trees from a dictionary spec.
- Create the same directory tree locally.
- Upload a local tree to a blob prefix, preserving structure.
- Optional `.keep` placeholders for visibility in storage tools.

## Install (local dev)

```bash
pip install -e .
```

## Usage

```python
from blob_actions import ConnectBlob

tree = {
    "data": {
        "incoming": {},
        "test": {},
        "train": {},
    },
    "output": {},
    "report": {},
}

client = ConnectBlob(
    connection_string="DefaultEndpointsProtocol=...",
    container_name="my-container",
)

# Create blob prefixes (with .keep placeholders)
client.ensure_tree("document_classification/credit/sme-origination", tree)

# Create the same structure locally
client.create_local_tree("/tmp/project", tree)

# Upload local files to blob, removing .keep placeholders if present
client.upload_tree(
    local_root="/tmp/project",
    blob_prefix="document_classification/credit/sme-origination",
)
```

## API

`ConnectBlob(connection_string: str, container_name: str)`

- `ensure_path(prefix: str, placeholders: bool = True) -> None`
  Creates a single prefix. If `placeholders` is `True`, writes `.keep` inside
  the prefix so it appears as a folder.

- `ensure_tree(base_prefix: str, tree_spec: dict, placeholders: bool = True) -> None`
  Creates all leaf prefixes under `base_prefix` using a dictionary tree spec.

- `create_local_tree(local_root: str, tree_spec: dict) -> None`
  Creates the local folder skeleton for the same tree spec.

- `upload_tree(local_root: str, blob_prefix: str, overwrite: bool = True,
  ignore_hidden: bool = True, remove_keep: bool = True) -> None`
  Uploads all local files under `local_root` into `blob_prefix`. If
  `remove_keep` is `True`, removes `.keep` placeholders under uploaded prefixes.

- `delete_file(blob_name: str) -> None`
  Deletes a single blob. Missing blobs are ignored.

- `delete_folder(prefix: str) -> None`
  Deletes all blobs under a prefix (including `.keep`). Missing containers or
  blobs are ignored.

## Snippets

```python
from blob_actions import ConnectBlob

client = ConnectBlob(
    connection_string="DefaultEndpointsProtocol=...",
    container_name="my-container",
)
```

```python
# ensure_path
client.ensure_path("document_classification/credit/sme-origination")
```

```python
# ensure_tree
tree = {
    "data": {
        "incoming": {},
        "test": {},
        "train": {},
    },
    "output": {},
    "report": {},
}
client.ensure_tree("document_classification/credit/sme-origination", tree)
```

```python
# create_local_tree
client.create_local_tree("/tmp/project", tree)
```

```python
# upload_tree
client.upload_tree(
    local_root="/tmp/project",
    blob_prefix="document_classification/credit/sme-origination",
)
```

```python
# delete_file
client.delete_file("document_classification/credit/sme-origination/data/incoming/file.csv")
```

```python
# delete_folder
client.delete_folder("document_classification/credit/sme-origination/data/incoming")
```

## Tree spec format

Dictionary-only format:

```python
{
  "data": {
    "incoming": {},
    "test": {},
    "train": {},
  },
  "output": {},
  "report": {}
}
```
