"""
Frontend Hot Updater

Safe frontend hot update with:
- Staging directory (extract before swap)
- Manifest-based version compatibility check
- Atomic swap (dist → dist_prev, dist_staging → dist)
- File-system health probe
- Automatic rollback on failure
- Crash counter for startup auto-rollback
"""

import json
import os
import shutil
import tarfile
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp

from services.infra.updater.constants import GITHUB_API_BASE, GITHUB_OWNER, GITHUB_REPO, utc_now
from services.infra.updater.models import FrontendVersion
from services.infra.updater.version import compare_versions

logger = logging.getLogger(__name__)

# Asset filename in GitHub release
FRONTEND_ASSET_NAME = "frontend-dist.tar.gz"

# Crash threshold: auto-rollback after this many consecutive crashes
CRASH_THRESHOLD = 3


class FrontendUpdater:
    """
    Manages frontend hot updates from GitHub releases.

    Downloads frontend-dist.tar.gz from GitHub releases and installs
    to ~/.flyto/frontend/dist/ using a safe staging + atomic swap strategy.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize updater with base directory for frontend assets."""
        self.base_dir = base_dir or Path.home() / ".flyto"
        self.frontend_dir = self.base_dir / "frontend"
        self.cache_dir = self.base_dir / "cache"

        self.frontend_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def frontend_path(self) -> Optional[Path]:
        """
        Get path to hot-updated frontend dist if it exists.

        Returns:
            ~/.flyto/frontend/dist/ if it exists and has content, else None
        """
        dist_dir = self.frontend_dir / "dist"
        if dist_dir.exists() and (dist_dir / "index.html").exists():
            return dist_dir
        return None

    @property
    def current_version(self) -> Optional[str]:
        """Get currently installed frontend version from marker file."""
        version_file = self.frontend_dir / "version.txt"
        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
        return None

    # =========================================================================
    # Update check
    # =========================================================================

    async def check_for_updates(self, app_version: str) -> Optional[FrontendVersion]:
        """
        Check GitHub releases for a newer frontend-dist.tar.gz.

        Args:
            app_version: Current app version to compare against

        Returns:
            FrontendVersion if update available, None otherwise
        """
        try:
            timeout = aiohttp.ClientTimeout(total=15, connect=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = "{}/repos/{}/{}/releases/latest".format(
                    GITHUB_API_BASE, GITHUB_OWNER, GITHUB_REPO
                )
                headers = {"Accept": "application/vnd.github.v3+json"}

                github_token = os.environ.get("GITHUB_TOKEN")
                if github_token:
                    headers["Authorization"] = "token {}".format(github_token)

                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        logger.warning("GitHub API returned %d", resp.status)
                        return None

                    data = await resp.json()

                release_version = data.get("tag_name", "")

                # Check if the release is newer than current frontend version
                current_fe = self.current_version
                if current_fe and compare_versions(release_version, current_fe) <= 0:
                    logger.debug("Frontend already up to date: %s", current_fe)
                    return None

                # Find frontend-dist.tar.gz asset
                assets = data.get("assets", [])
                for asset in assets:
                    if asset.get("name") == FRONTEND_ASSET_NAME:
                        return FrontendVersion(
                            version=release_version,
                            download_url=asset["browser_download_url"],
                            published_at=data.get("published_at", ""),
                        )

                logger.debug("No %s asset found in release %s", FRONTEND_ASSET_NAME, release_version)
                return None

        except aiohttp.ClientError as e:
            logger.error("Network error checking frontend updates: %s", e)
            return None
        except Exception as e:
            logger.error("Error checking frontend updates: %s", e)
            return None

    # =========================================================================
    # Download and install (safe pipeline)
    # =========================================================================

    async def download_and_install(self, version: FrontendVersion) -> bool:
        """
        Safe frontend update pipeline:
        Download → Staging → Validate → Atomic Swap → Health Probe → Rollback on failure

        Args:
            version: FrontendVersion with download_url

        Returns:
            True if successful
        """
        logger.info("Starting safe frontend update to %s...", version.version)

        dist_dir = self.frontend_dir / "dist"
        staging_dir = self.frontend_dir / "dist_staging"
        prev_dir = self.frontend_dir / "dist_prev"

        try:
            # Step 1: Download tarball to cache
            tarball_path = await self._download_tarball(version)
            if not tarball_path:
                return False

            # Step 2: Extract to staging directory
            if not self._extract_tarball(tarball_path, staging_dir):
                self._cleanup_dir(staging_dir)
                return False

            # Step 3: Read manifest and check compatibility
            manifest = self._read_manifest(staging_dir)
            if manifest:
                from config.constants import APP_VERSION
                if not self._check_compatibility(manifest, APP_VERSION):
                    logger.warning(
                        "Frontend %s requires backend >= %s, current is %s — skipping",
                        version.version,
                        manifest.get("min_backend_version", "?"),
                        APP_VERSION,
                    )
                    self._cleanup_dir(staging_dir)
                    return False

            # Step 4: Atomic swap
            #   dist/ → dist_prev/ (backup current)
            #   dist_staging/ → dist/ (activate new)
            if not self._atomic_swap(dist_dir, staging_dir, prev_dir):
                return False

            # Step 5: Health probe on new dist/
            if not self._health_check(dist_dir, manifest):
                logger.error("Health check failed after swap — rolling back")
                self._rollback(dist_dir, prev_dir)
                return False

            # Step 6: Write version marker
            version_file = self.frontend_dir / "version.txt"
            version_file.write_text(version.version, encoding="utf-8")

            # Step 7: Cleanup tarball (keep dist_prev for future rollback)
            tarball_path.unlink(missing_ok=True)

            # Reset crash counter for new version
            self.clear_crash_counter()

            logger.info("Successfully installed frontend %s", version.version)
            return True

        except Exception as e:
            logger.error("Error installing frontend %s: %s", version.version, e)
            # Attempt rollback if dist is missing but prev exists
            if not dist_dir.exists() and prev_dir.exists():
                logger.info("Restoring previous frontend from dist_prev")
                try:
                    prev_dir.rename(dist_dir)
                except Exception as re:
                    logger.error("Rollback also failed: %s", re)
            self._cleanup_dir(staging_dir)
            return False

    # =========================================================================
    # Helper methods
    # =========================================================================

    async def _download_tarball(self, version: FrontendVersion) -> Optional[Path]:
        """Download tarball to cache directory."""
        logger.info("Downloading frontend %s...", version.version)
        tarball_path = self.cache_dir / FRONTEND_ASSET_NAME

        try:
            timeout = aiohttp.ClientTimeout(total=300, connect=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {"Accept": "application/octet-stream"}

                github_token = os.environ.get("GITHUB_TOKEN")
                if github_token:
                    headers["Authorization"] = "token {}".format(github_token)

                async with session.get(version.download_url, headers=headers) as resp:
                    if resp.status != 200:
                        logger.error("Failed to download frontend: HTTP %d", resp.status)
                        return None

                    with open(tarball_path, 'wb') as f:
                        while True:
                            chunk = await resp.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)

            return tarball_path

        except Exception as e:
            logger.error("Download failed: %s", e)
            tarball_path.unlink(missing_ok=True)
            return None

    def _extract_tarball(self, tarball_path: Path, staging_dir: Path) -> bool:
        """Extract tarball to staging directory with path safety checks."""
        # Clean staging if leftover from previous attempt
        self._cleanup_dir(staging_dir)
        staging_dir.mkdir(parents=True, exist_ok=True)

        try:
            with tarfile.open(tarball_path, 'r:gz') as tf:
                for member in tf.getmembers():
                    # Security: reject unsafe paths
                    if member.name.startswith('/') or '..' in member.name:
                        logger.error("Unsafe path in tarball: %s", member.name)
                        return False
                    # Reject absolute or upward-traversal resolved paths
                    resolved = (staging_dir / member.name).resolve()
                    if not str(resolved).startswith(str(staging_dir.resolve())):
                        logger.error("Path traversal detected: %s", member.name)
                        return False
                tf.extractall(staging_dir)

            logger.info("Extracted frontend to staging directory")
            return True

        except Exception as e:
            logger.error("Extraction failed: %s", e)
            return False

    def _read_manifest(self, staging_dir: Path) -> Optional[Dict[str, Any]]:
        """Read manifest.json from staging directory."""
        manifest_path = staging_dir / "manifest.json"
        if not manifest_path.exists():
            logger.debug("No manifest.json found in frontend bundle (optional)")
            return None

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to read manifest.json: %s", e)
            return None

    def _check_compatibility(self, manifest: Dict[str, Any], app_version: str) -> bool:
        """Check if frontend is compatible with current backend version."""
        min_backend = manifest.get("min_backend_version")
        if not min_backend:
            return True  # No constraint specified

        # app_version >= min_backend_version
        return compare_versions(app_version, min_backend) >= 0

    def _atomic_swap(self, dist_dir: Path, staging_dir: Path, prev_dir: Path) -> bool:
        """
        Atomic swap: dist → dist_prev, dist_staging → dist.

        Uses Path.rename() which is atomic on the same filesystem.
        """
        try:
            # Remove old dist_prev if exists (only one backup kept)
            if prev_dir.exists():
                shutil.rmtree(prev_dir, ignore_errors=True)

            # dist/ → dist_prev/ (backup current)
            if dist_dir.exists():
                dist_dir.rename(prev_dir)

            # dist_staging/ → dist/ (activate new)
            staging_dir.rename(dist_dir)

            logger.info("Atomic swap completed: staging → dist")
            return True

        except Exception as e:
            logger.error("Atomic swap failed: %s", e)
            # Attempt recovery: if dist is gone but prev exists, restore
            if not dist_dir.exists() and prev_dir.exists():
                try:
                    prev_dir.rename(dist_dir)
                    logger.info("Restored dist from dist_prev after swap failure")
                except Exception as re:
                    logger.error("Recovery also failed: %s", re)
            return False

    def _health_check(self, dist_dir: Path, manifest: Optional[Dict[str, Any]] = None) -> bool:
        """
        File-system health probe: verify critical files exist after swap.

        Checks:
        - index.html exists
        - At least one .js file in assets/
        - At least one .css file in assets/
        - manifest files if provided
        """
        # Must have index.html
        if not (dist_dir / "index.html").exists():
            logger.error("Health check: index.html missing")
            return False

        # Must have JS and CSS assets
        assets_dir = dist_dir / "assets"
        if assets_dir.exists():
            js_files = list(assets_dir.glob("*.js"))
            css_files = list(assets_dir.glob("*.css"))
            if not js_files:
                logger.error("Health check: no .js files in assets/")
                return False
            if not css_files:
                logger.error("Health check: no .css files in assets/")
                return False

        # If manifest lists specific files, verify they exist
        if manifest and "files" in manifest:
            for fname in manifest["files"]:
                if not (dist_dir / fname).exists():
                    logger.error("Health check: manifest file missing: %s", fname)
                    return False

        logger.info("Health check passed")
        return True

    def _rollback(self, dist_dir: Path, prev_dir: Path) -> bool:
        """Rollback: dist → dist_failed, dist_prev → dist."""
        failed_dir = self.frontend_dir / "dist_failed"

        try:
            # Move broken dist to dist_failed for debugging
            if failed_dir.exists():
                shutil.rmtree(failed_dir, ignore_errors=True)
            if dist_dir.exists():
                dist_dir.rename(failed_dir)

            # Restore previous version
            if prev_dir.exists():
                prev_dir.rename(dist_dir)
                logger.info("Rollback successful: restored dist_prev → dist")
                return True
            else:
                logger.error("Rollback failed: no dist_prev available")
                return False

        except Exception as e:
            logger.error("Rollback failed: %s", e)
            return False

    # =========================================================================
    # Crash detection + auto-rollback
    # =========================================================================

    @property
    def _crash_counter_path(self) -> Path:
        """Path to the crash counter JSON file."""
        return self.frontend_dir / "crash_counter.json"

    def _read_crash_counter(self) -> Dict[str, Any]:
        """Read crash counter from disk."""
        path = self._crash_counter_path
        if not path.exists():
            return {"count": 0, "version": "", "last_crash": ""}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"count": 0, "version": "", "last_crash": ""}

    def _write_crash_counter(self, data: Dict[str, Any]):
        """Write crash counter to disk."""
        try:
            with open(self._crash_counter_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning("Failed to write crash counter: %s", e)

    def increment_crash_counter(self):
        """Increment crash counter for current version."""
        current = self.current_version or ""
        counter = self._read_crash_counter()

        # Reset if version changed
        if counter.get("version") != current:
            counter = {"count": 0, "version": current, "last_crash": ""}

        counter["count"] = counter.get("count", 0) + 1
        counter["last_crash"] = utc_now().isoformat()
        self._write_crash_counter(counter)

    def clear_crash_counter(self):
        """Clear crash counter (call after successful load)."""
        path = self._crash_counter_path
        if path.exists():
            path.unlink(missing_ok=True)

    def should_rollback_on_startup(self) -> bool:
        """Check if we should auto-rollback due to repeated crashes."""
        prev_dir = self.frontend_dir / "dist_prev"
        if not prev_dir.exists():
            return False  # Nothing to rollback to

        counter = self._read_crash_counter()
        current = self.current_version or ""

        # Only rollback if same version crashed repeatedly
        if counter.get("version") != current:
            return False

        return counter.get("count", 0) >= CRASH_THRESHOLD

    def auto_rollback(self) -> bool:
        """Auto-rollback to dist_prev due to crash history."""
        dist_dir = self.frontend_dir / "dist"
        prev_dir = self.frontend_dir / "dist_prev"

        if not prev_dir.exists():
            logger.error("Auto-rollback: no dist_prev available")
            return False

        logger.warning("Auto-rolling back frontend due to %d crashes", CRASH_THRESHOLD)

        if self._rollback(dist_dir, prev_dir):
            # Read previous version from dist if available
            prev_version_manifest = dist_dir / "manifest.json"
            if prev_version_manifest.exists():
                try:
                    with open(prev_version_manifest, 'r', encoding='utf-8') as f:
                        m = json.load(f)
                    prev_ver = m.get("version", "")
                    if prev_ver:
                        version_file = self.frontend_dir / "version.txt"
                        version_file.write_text(prev_ver, encoding="utf-8")
                except Exception:
                    pass

            self.clear_crash_counter()
            return True

        return False

    # =========================================================================
    # Utility
    # =========================================================================

    @staticmethod
    def _cleanup_dir(path: Path):
        """Remove a directory if it exists."""
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
