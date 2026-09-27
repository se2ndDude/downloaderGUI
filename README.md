# LinkDrop — Android social downloader

A flat, light Android downloader UI powered by the `yt-dlp` Python library.

## Included

- URL paste + one-tap analyze
- Download action with percentage / speed / ETA display
- Carousel / multi-entry downloads are kept enabled
- Android 10+ Downloads saving through MediaStore
- Older Android fallback to the public `Download` directory
- Blue / purple / black visual theme
- Custom app icon
- GitHub Actions workflow that runs a Python compile check and builds APKs
- APK architectures: `arm64-v8a`, `armeabi-v7a`, `x86_64`

## Build on GitHub

1. Create a new GitHub repository.
2. Upload the contents of this folder.
3. Push to any branch or run **Actions → Build LinkDrop APK → Run workflow**.
4. Open the completed workflow run and download the **LinkDrop-APKs** artifact.

The build uses Buildozer 1.5.0 and pinned Kivy / yt-dlp versions for reproducibility.

## Important

The app uses yt-dlp's site extractors, so which links work depends on the current support and requirements of each site. Site changes can require a newer yt-dlp release. The bundled version can be changed in `buildozer.spec` and the GitHub workflow when needed.

Use the app only for content you are allowed to download and in accordance with each platform's terms.
