# Deployment

The platform is designed to be statically hosted via GitHub Pages.
- A GitHub Action workflow (`.github/workflows/deploy_pages.yml`) runs automatically on push to the active branch.
- It deploys the `web` folder.
- No backend server is required; all interactions are processed client-side.
