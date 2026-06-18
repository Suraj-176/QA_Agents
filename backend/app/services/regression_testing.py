import os
import cv2
import numpy as np
from datetime import datetime
from sqlalchemy.orm import Session
from playwright.async_api import async_playwright
from app.models import Baseline, BaselineScreenshot, RegressionTestRun, RegressionTestResult

VIEWPORTS = {
    "desktop": {"width": 1920, "height": 1080},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 375, "height": 667}
}

class RegressionTestingService:
    def __init__(self):
        # Configure local directory where files are hosted
        self.static_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
            "static"
        )
        os.makedirs(self.static_dir, exist_ok=True)

    def _compare_images(self, baseline_path: str, run_path: str, diff_output_path: str) -> tuple:
        """
        Loads baseline and target run images, computes absolute visual differences,
        and generates a blended overlay highlighting mismatches in red.
        Returns: (similarity_score: float, is_mismatch: bool)
        """
        base_img = cv2.imread(baseline_path)
        run_img = cv2.imread(run_path)

        if base_img is None or run_img is None:
            raise ValueError(f"Could not read comparison images. Baseline: {baseline_path}, Run: {run_path}")

        # Ensure identical sizes for visual subtraction
        if base_img.shape != run_img.shape:
            run_img = cv2.resize(run_img, (base_img.shape[1], base_img.shape[0]))

        # Convert to grayscale to simplify subtraction and calculation
        base_gray = cv2.cvtColor(base_img, cv2.COLOR_BGR2GRAY)
        run_gray = cv2.cvtColor(run_img, cv2.COLOR_BGR2GRAY)

        # Calculate pixel difference
        abs_diff = cv2.absdiff(base_gray, run_gray)

        # Threshold difference image to segment shifts
        _, thresh = cv2.threshold(abs_diff, 15, 255, cv2.THRESH_BINARY)

        # Calculate percentage similarity
        total_pixels = thresh.size
        mismatched_pixels = np.count_nonzero(thresh)
        similarity = (1.0 - (mismatched_pixels / total_pixels)) * 100.0

        # High similarity limit (any score below 99.5 is classified as a layout regression)
        is_mismatch = similarity < 99.5

        # Create color highlight overlay (White pixels turned to RED)
        highlight_mask = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        highlight_mask[thresh == 255] = [0, 0, 255] # Red outline in BGR

        # Blend original target image with red mask
        blended_diff = cv2.addWeighted(run_img, 0.7, highlight_mask, 0.3, 0)
        cv2.imwrite(diff_output_path, blended_diff)

        return round(similarity, 2), is_mismatch

    async def _capture_screenshots(self, url: str, base_folder: str) -> dict:
        """
        Launches Playwright headless browser and captures mobile, tablet, and desktop views.
        """
        os.makedirs(base_folder, exist_ok=True)
        captured_paths = {}

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            for name, viewport in VIEWPORTS.items():
                await page.set_viewport_size(viewport)
                
                try:
                    # Navigate and wait for network stability to ensure complete rendering
                    await page.goto(url, timeout=30000, wait_until="networkidle")
                except Exception as goto_err:
                    # Fallback to domcontentloaded if network stays busy
                    try:
                        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    except Exception:
                        await browser.close()
                        raise RuntimeError(f"Failed to load website {url}: {str(goto_err)}")

                # Small delay for web font/animation layout stabilization
                await page.wait_for_timeout(1000)

                target_filename = f"{name}.png"
                target_filepath = os.path.join(base_folder, target_filename)
                
                # Perform screenshot capture
                await page.screenshot(path=target_filepath)
                captured_paths[name] = target_filepath

            await browser.close()
        return captured_paths

    async def setup_baseline(self, name: str, url: str, db: Session) -> dict:
        """
        Creates a baseline visual model, takes desktop/tablet/mobile snaps, and registers details in SQLite.
        """
        # 1. Create Baseline instance
        baseline = Baseline(name=name, url=url)
        db.add(baseline)
        db.flush()

        # Build clean directory structure: static/baselines/{id}/
        baseline_folder = os.path.join(self.static_dir, "baselines", str(baseline.id))
        
        try:
            # 2. Capture baseline screenshots
            captured_files = await self._capture_screenshots(url, baseline_folder)
            
            # 3. Save BaselineScreenshot entries
            for viewport, path in captured_files.items():
                # Store relative paths for easier static serving across hosts
                relative_path = os.path.relpath(path, self.static_dir).replace("\\", "/")
                screen_record = BaselineScreenshot(
                    baseline_id=baseline.id,
                    viewport=viewport,
                    image_path=relative_path
                )
                db.add(screen_record)
            
            db.commit()
            return {
                "baseline_id": baseline.id,
                "name": baseline.name,
                "url": baseline.url,
                "screenshots_count": len(captured_files)
            }
        except Exception as e:
            db.rollback()
            # Clean up files created prior to rollback
            if os.path.exists(baseline_folder):
                import shutil
                shutil.rmtree(baseline_folder, ignore_errors=True)
            raise e

    async def run_regression_test(self, run_id: int, db: Session):
        """
        Executes comparison screenshot capture and CV visual subtraction in background.
        Updates state of RegressionTestRun record on completion or failure.
        """
        run = db.query(RegressionTestRun).filter(RegressionTestRun.id == run_id).first()
        if not run:
            return

        run.status = "running"
        db.commit()

        run_folder = os.path.join(self.static_dir, "runs", str(run.id))
        
        try:
            # 1. Capture snapshots of the new target URL
            target_snaps = await self._capture_screenshots(run.target_url, run_folder)
            
            # 2. Extract baseline screenshot files
            baseline = db.query(Baseline).filter(Baseline.id == run.baseline_id).first()
            if not baseline or not baseline.screenshots:
                raise ValueError(f"Baseline {run.baseline_id} does not contain screenshots.")

            baseline_map = {s.viewport: s.image_path for s in baseline.screenshots}

            mismatch_count = 0
            viewports_run = 0

            # 3. Compare each viewport using OpenCV
            for viewport, run_filepath in target_snaps.items():
                base_rel_path = baseline_map.get(viewport)
                if not base_rel_path:
                    continue # Skip if no baseline capture exists for viewport
                
                base_filepath = os.path.join(self.static_dir, base_rel_path)
                diff_filename = f"diff_{viewport}.png"
                diff_filepath = os.path.join(run_folder, diff_filename)

                # Execute Image Comparison
                similarity, is_mismatch = self._compare_images(
                    baseline_path=base_filepath,
                    run_path=run_filepath,
                    diff_output_path=diff_filepath
                )

                if is_mismatch:
                    mismatch_count += 1

                # Save relative paths to DB
                run_rel_path = os.path.relpath(run_filepath, self.static_dir).replace("\\", "/")
                diff_rel_path = os.path.relpath(diff_filepath, self.static_dir).replace("\\", "/")

                test_result = RegressionTestResult(
                    run_id=run.id,
                    viewport=viewport,
                    similarity_score=similarity,
                    baseline_image_path=base_rel_path,
                    run_image_path=run_rel_path,
                    diff_image_path=diff_rel_path,
                    is_mismatch=is_mismatch
                )
                db.add(test_result)
                viewports_run += 1

            # 4. Record summary data
            run.status = "completed"
            if mismatch_count > 0:
                run.summary = f"Visual Regressions Detected! {mismatch_count} out of {viewports_run} viewports failed comparison checks."
            else:
                run.summary = f"Success. All {viewports_run} viewports successfully validated and matched visual baselines."

        except Exception as e:
            run.status = "failed"
            run.summary = f"Execution interrupted. Error: {str(e)}"
        finally:
            db.commit()
