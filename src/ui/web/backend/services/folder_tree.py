"""Utilities for template folder trees."""


def children_by_parent(folders) -> dict:
    children = {}
    for folder in folders:
        children.setdefault(getattr(folder, "parent_id", None), []).append(folder)
    return children


def descendant_ids(children: dict, folder_id: str) -> set[str]:
    ids = {folder_id}
    stack = [folder_id]
    while stack:
        current = stack.pop()
        for child in children.get(current, []):
            if child.id in ids:
                continue
            ids.add(child.id)
            stack.append(child.id)
    return ids


def descendant_folder_ids(folders, folder_id: str) -> set[str]:
    return descendant_ids(children_by_parent(folders), folder_id)


def folder_path(folder, folders_by_id: dict) -> list[str]:
    path = []
    current = folder
    seen = set()
    while current and current.id not in seen:
        seen.add(current.id)
        path.append(current.name)
        current = folders_by_id.get(getattr(current, "parent_id", None))
    return list(reversed(path))
