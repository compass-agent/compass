# Releasing Compass

Compass is distributed as a Windows installer named:

```text
Compass-Setup-<version>.exe
```

The website download button reads the latest GitHub release through the GitHub
API. After a release contains a Windows `.exe` installer asset, the website
updates automatically without editing `docs/index.html`.

## Preferred Flow: Tag-Based Release

1. Update the version in `package.json`.
2. Commit the change.
3. Create and push a version tag:

```bash
git tag v<version>
git push origin main
git push origin v<version>
```

The `Release Windows Installer` GitHub Actions workflow builds on Windows,
uploads the installer as a workflow artifact, and publishes the tagged GitHub
release with the installer attached.

Use this tag format:

```text
v1.2.3
```

## Manual Local Build

Use this when testing a release locally or when GitHub Actions is unavailable.

```bash
npm run dist:win
```

This runs:

1. PyInstaller, which bundles the Python backend to `backend/dist/Compass Backend/`.
2. webpack, which builds the production renderer bundle.
3. electron-builder, which creates `dist/Compass-Setup-<version>.exe`.

## Release Sanity Check

On a Windows machine or clean user account with SAP2000 installed:

- [ ] Install Compass from `dist/Compass-Setup-<version>.exe`.
- [ ] Launch Compass from the Start Menu or desktop shortcut.
- [ ] First-run key setup appears, validates, and saves.
- [ ] Open SAP2000 first.
- [ ] In Compass, use `Tools -> SAP2000 Scripting -> Connect`.
- [ ] The SAP2000 status turns connected without opening a second SAP2000 instance.
- [ ] Send a minimal prompt such as `Tell me whether you are connected to SAP2000`.
- [ ] Run one tiny SAP2000 action, such as creating a blank model/project.
- [ ] Close Compass and confirm no orphan `Compass Backend.exe` or `compass_backend.exe` remains in Task Manager.

Run Compass and SAP2000 at the same Windows privilege level. If one is elevated
and the other is not, COM attach can fail.

## Manual GitHub Release Fallback

If you built locally and need to publish by hand:

```bash
gh release create v<version> "dist/Compass-Setup-<version>.exe" \
  --title "Compass v<version>" \
  --notes "Highlights of this release..."
```

Or use the GitHub web UI:

1. Open GitHub Releases.
2. Draft a new release.
3. Create or select tag `v<version>`.
4. Attach `dist/Compass-Setup-<version>.exe`.
5. Publish.

The release should contain exactly one primary Windows installer whose filename
ends in `.exe`. The website prefers an asset matching `Compass-Setup-*.exe`.

## Website Verification

After publishing:

1. Open `https://compass-agent.github.io/compass/#download`.
2. Confirm the card shows the new version, date, and installer size.
3. Click the download button and confirm it downloads the `.exe` release asset.
4. Hard-refresh the browser if the page is cached.

## Website Deployment

The public site lives in `docs/` on `main` and is served by GitHub Pages. It is a
single hand-written static page with no build step.
