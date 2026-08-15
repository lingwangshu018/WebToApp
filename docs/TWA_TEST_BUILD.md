# Manual TWA test build

The `TWA Test Build` workflow is a quick way to validate the immersive TWA runtime without first deploying the full WebToApp backend.

1. Open **Actions → TWA Test Build → Run workflow**.
2. Enter an HTTPS URL, app name, and Android package name.
3. Wait for the build job to finish.
4. Download the `twa-test-*` artifact. It contains:
   - `android.apk`
   - `assetlinks.json`
5. Deploy `assetlinks.json` to the wrapped origin at `/.well-known/assetlinks.json`.
6. Install the APK from the same workflow run and test it on Android.

The test workflow creates an ephemeral signing key on the GitHub runner. Therefore each new workflow run may produce a different certificate fingerprint. Always use the `assetlinks.json` from the same run as the APK. The production WebToApp backend instead keeps a stable per-app keystore so updates preserve the same signing identity.
