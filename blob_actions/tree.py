import os
from typing import Dict, Iterable, List


def collect_leaf_prefixes(base_prefix: str, tree_spec: Dict) -> List[str]:
    leaves: List[str] = []
    _walk_tree(base_prefix, tree_spec, leaves)
    return leaves


def create_local_tree(local_root: str, tree_spec: Dict) -> None:
    for path in collect_leaf_prefixes("", tree_spec):
        full_path = os.path.join(local_root, path)
        os.makedirs(full_path, exist_ok=True)


def is_hidden_path(path: str) -> bool:
    for segment in path.replace("\\", "/").split("/"):
        if segment.startswith(".") and segment not in (".", ".."):
            return True
    return False


def _walk_tree(prefix: str, tree_spec: Dict, leaves: List[str]) -> None:
    if not isinstance(tree_spec, dict):
        raise ValueError("tree_spec must be a dictionary")
    if not tree_spec:
        leaves.append(prefix.strip("/"))
        return
    for name, subtree in tree_spec.items():
        if not isinstance(name, str) or not name:
            raise ValueError("tree_spec keys must be non-empty strings")
        next_prefix = join_prefix(prefix, name)
        if not isinstance(subtree, dict):
            raise ValueError("tree_spec values must be dictionaries")
        _walk_tree(next_prefix, subtree, leaves)


def join_prefix(prefix: str, name: str) -> str:
    if not prefix:
        return name.strip("/")
    return prefix.strip("/") + "/" + name.strip("/")
