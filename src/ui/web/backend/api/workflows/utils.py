"""
Workflow Utilities

Shared helper functions for workflow execution and validation.
"""


def normalize_template_module(module_id: str, params: dict) -> tuple:
    """
    Normalize template module IDs to canonical form.

    Handles formats:
      - template.invoke:xxx → template.invoke + {template_id: xxx}
      - template.xxx → template.invoke + {template_id: xxx}
      - template.invoke (already canonical, ensures library_id is set)

    Returns:
        (module_id, params) tuple with normalized values.
    """
    if not module_id:
        return module_id, params

    if module_id.startswith("template.invoke:"):
        template_id = module_id.replace("template.invoke:", "")
        new_params = {**params}
        if "params" not in new_params:
            new_params["params"] = {}
        new_params["params"]["template_id"] = template_id
        new_params["params"]["library_id"] = template_id
        return "template.invoke", new_params

    if module_id.startswith("template.") and module_id != "template.invoke":
        template_id = module_id.replace("template.", "")
        new_params = {**params}
        if "params" not in new_params:
            new_params["params"] = {}
        new_params["params"]["template_id"] = template_id
        new_params["params"]["library_id"] = template_id
        return "template.invoke", new_params

    # Already template.invoke — ensure library_id is set
    if module_id == "template.invoke":
        inner_params = params.get("params", {})
        template_id = inner_params.get("template_id") or inner_params.get("templateId")
        if template_id and not inner_params.get("library_id"):
            new_params = {**params}
            new_params["params"] = {**inner_params, "library_id": template_id}
            return module_id, new_params

    return module_id, params
