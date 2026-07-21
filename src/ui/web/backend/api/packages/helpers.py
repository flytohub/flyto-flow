"""
Backward compatibility — split into sub-modules.

- package_ops.py        — package installation/update/removal operations
- package_validation.py — validation and registry helpers
"""

from .package_defs import (  # noqa: F401
    SYSTEM_PACKAGES,
    _PACKAGES_BY_ID,
    _IS_FROZEN,
    _PIP_TARGET_DIR,
    _CACHE_DIR,
    _load_auto_update_settings,
    _save_auto_update_settings,
    _get_installed_version,
    _get_version_from_dist_info,
    _get_chromium_version,
)

from .package_ops import (  # noqa: F401
    _get_pypi_wheel_info,
    _download_and_install_wheel,
    _run_subprocess,
    _hot_update_core,
    _pip_install_dev,
    _install_or_update_package,
    _install_chromium,
    _remove_package_impl,
    _remove_chromium,
    _remove_from_target_dir,
)

from .package_validation import (  # noqa: F401
    _check_pypi_latest,
)
