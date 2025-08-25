# GitHub Actions CI/CD Setup

This project uses GitHub Actions to automatically build and publish Docker images to Docker Hub.

## Setup Instructions

### 1. Configure Docker Hub Secrets

You need to add the following secrets to your GitHub repository:

1. Go to your GitHub repository
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Add the following **Repository secrets**:

   - `DOCKER_USERNAME`: Your Docker Hub username
   - `DOCKER_PASSWORD`: Your Docker Hub access token (not your password!)

### 2. Create Docker Hub Access Token

1. Go to [Docker Hub](https://hub.docker.com/)
2. Sign in to your account
3. Go to **Account Settings** → **Security**
4. Click **New Access Token**
5. Give it a descriptive name (e.g., "GitHub Actions")
6. Select appropriate permissions (Read, Write, Delete)
7. Copy the generated token and use it as `DOCKER_PASSWORD` secret

### 3. Workflow Triggers

The workflow will trigger on:

- **Push to master/main branch**: Builds and pushes with `latest` tag
- **Push tags starting with 'v'**: Builds and pushes with version tags (e.g., `v1.0.0`)
- **Pull requests**: Builds only (doesn't push to registry)
- **Manual trigger**: Can be run manually with custom options

#### Manual Workflow Dispatch

You can manually trigger the workflow from GitHub:

1. Go to your repository → **Actions** tab
2. Select "Build and Publish Docker Image" workflow
3. Click **Run workflow** button
4. Configure options:
   - **Custom Docker tag**: Optional custom tag (default: `manual`)
   - **Target platforms**: Choose architecture (`linux/amd64,linux/arm64`, `linux/amd64`, or `linux/arm64`)
   - **Push to Docker Hub**: Whether to push the built image (default: `true`)

This is useful for:
- Testing builds without creating commits/tags
- Building specific platform images
- Creating custom tagged releases

### 4. Multi-Architecture Support

The workflow builds images for both:
- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64/Apple Silicon)

### 5. Tagging Strategy

- **Branch pushes**: Tagged with branch name
- **Version tags**: Tagged with semantic version (`v1.0.0` → `1.0.0`, `1.0`, `1`, `latest`)
- **Pull requests**: Tagged with PR number

## Manual Release Process

To create a new release:

1. Update version in your code if needed
2. Create and push a git tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. The workflow will automatically build and push the new version

## Monitoring

- Check the **Actions** tab in your GitHub repository to monitor workflow runs
- Failed builds will send notifications to repository admins
- Build logs are available for debugging

## Image Usage

After successful build, your images will be available at:
```bash
docker pull lihongjie0209/hanzi-similar:latest
docker pull lihongjie0209/hanzi-similar:v1.0.0
```
