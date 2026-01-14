import os
from typing import Dict, Iterable, List, Optional, Set

from azure.core.exceptions import HttpResponseError, ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

from blob_actions.tree import collect_leaf_prefixes, create_local_tree, is_hidden_path, join_prefix


class ConnectBlob:
    def __init__(self, connection_string: str, container_name: str):
        if not connection_string:
            raise ValueError("connection_string is required")
        if not container_name:
            raise ValueError("container_name is required")
        self.connection_string = connection_string
        self.container_name = container_name
        self._service_client = BlobServiceClient.from_connection_string(connection_string)

    def ensure_path(self, prefix: str, placeholders: bool = True) -> None:
        self._ensure_container()
        prefix = prefix.strip("/")
        if not placeholders or not prefix:
            return
        self._ensure_placeholder(prefix)

    def ensure_tree(self, base_prefix: str, tree_spec: Dict, placeholders: bool = True) -> None:
        self._ensure_container()
        leaf_prefixes = collect_leaf_prefixes(base_prefix.strip("/"), tree_spec)
        if not placeholders:
            return
        for prefix in leaf_prefixes:
            if prefix:
                self._ensure_placeholder(prefix)

    def create_local_tree(self, local_root: str, tree_spec: Dict) -> None:
        os.makedirs(local_root, exist_ok=True)
        create_local_tree(local_root, tree_spec)

    def upload_tree(
        self,
        local_root: str,
        blob_prefix: str,
        overwrite: bool = True,
        ignore_hidden: bool = True,
        remove_keep: bool = True,
    ) -> None:
        self._ensure_container()
        local_root = os.path.abspath(local_root)
        if not os.path.isdir(local_root):
            raise FileNotFoundError(local_root)

        blob_prefix = blob_prefix.strip("/")
        uploaded_prefixes: Set[str] = set()
        for root, _, filenames in os.walk(local_root):
            for filename in filenames:
                local_path = os.path.join(root, filename)
                rel_path = os.path.relpath(local_path, local_root)
                if ignore_hidden and is_hidden_path(rel_path):
                    continue
                blob_name = join_prefix(blob_prefix, _to_blob_path(rel_path))
                blob_client = self._service_client.get_blob_client(
                    self.container_name, blob_name
                )
                with open(local_path, "rb") as handle:
                    blob_client.upload_blob(handle, overwrite=overwrite)
                prefix = os.path.dirname(blob_name).replace("\\", "/")
                if prefix:
                    uploaded_prefixes.add(prefix)

        if remove_keep:
            self._remove_placeholders(uploaded_prefixes)

    def delete_file(self, blob_name: str) -> None:
        blob_name = blob_name.strip("/")
        if not blob_name:
            raise ValueError("blob_name is required")
        blob_client = self._service_client.get_blob_client(self.container_name, blob_name)
        try:
            blob_client.delete_blob()
        except ResourceNotFoundError:
            pass

    def delete_folder(self, prefix: str) -> None:
        prefix = prefix.strip("/")
        if prefix:
            name_starts_with = prefix + "/"
        else:
            name_starts_with = ""
        container_client = self._service_client.get_container_client(self.container_name)
        try:
            blob_names = [
                blob.name
                for blob in container_client.list_blobs(name_starts_with=name_starts_with)
            ]
        except ResourceNotFoundError:
            return
        for blob_name in sorted(blob_names, key=len, reverse=True):
            try:
                container_client.delete_blob(blob_name)
            except ResourceNotFoundError:
                pass
            except HttpResponseError as exc:
                if getattr(exc, "error_code", None) == "DirectoryNotEmpty":
                    continue
                raise

    def _ensure_container(self) -> None:
        try:
            self._service_client.create_container(self.container_name)
        except ResourceExistsError:
            pass

    def _ensure_placeholder(self, prefix: str) -> None:
        blob_name = join_prefix(prefix, ".keep")
        blob_client = self._service_client.get_blob_client(self.container_name, blob_name)
        try:
            blob_client.upload_blob(b"", overwrite=False)
        except ResourceExistsError:
            pass

    def _remove_placeholders(self, prefixes: Iterable[str]) -> None:
        for prefix in prefixes:
            blob_name = join_prefix(prefix, ".keep")
            blob_client = self._service_client.get_blob_client(self.container_name, blob_name)
            try:
                blob_client.delete_blob()
            except ResourceNotFoundError:
                pass


def _to_blob_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("/")
