# CI/CD Setup Guide 🚀

This guide helps you set up the complete CI/CD pipeline for the MCP Python Analyzer project.

## 📋 Prerequisites

Before enabling the full CI/CD pipeline, ensure you have:

- [x] GitHub repository with appropriate permissions
- [x] PyPI account for package publishing
- [x] TestPyPI account for testing (optional but recommended)

## 🔐 GitHub Repository Settings

### Required Permissions

Go to **Settings > Actions > General** and ensure:

- ✅ **Allow GitHub Actions to create and approve pull requests**
- ✅ **Allow GitHub Actions to approve pull requests**
- ✅ **Read and write permissions** for GITHUB_TOKEN

### Environments Setup

Create these environments in **Settings > Environments**:

#### 1. PyPI Environment

- **Name**: `pypi`
- **URL**: `https://pypi.org/p/mcp-server-analyzer`
- **Protection rules**:
  - ✅ Required reviewers (optional, for extra security)
  - ✅ Wait timer: 0 minutes
  - ✅ Restrict to protected branches only: `main`

#### 2. TestPyPI Environment

- **Name**: `testpypi`
- **URL**: `https://test.pypi.org/p/mcp-server-analyzer`
- **Protection rules**: None (for automatic testing)

## 🐍 PyPI Trusted Publishing Setup

### 1. PyPI Configuration

1. **Log in to [PyPI](https://pypi.org)**
2. **Go to Account Settings > Publishing**
3. **Add a new trusted publisher** with these settings:
   - **PyPI Project Name**: `mcp-server-analyzer`
   - **Owner**: `anselmoo` (your GitHub username)
   - **Repository name**: `mcp-server-analyzer`
   - **Workflow name**: `ci-cd.yml`
   - **Environment name**: `pypi`

### 2. TestPyPI Configuration (Optional)

1. **Log in to [TestPyPI](https://test.pypi.org)**
2. **Go to Account Settings > Publishing**
3. **Add a new trusted publisher** with these settings:
   - **PyPI Project Name**: `mcp-server-analyzer`
   - **Owner**: `anselmoo` (your GitHub username)
   - **Repository name**: `mcp-server-analyzer`
   - **Workflow name**: `ci-cd.yml`
   - **Environment name**: `testpypi`

## 🐳 Container Registry Setup

The pipeline automatically publishes to **GitHub Container Registry (GHCR)** using GITHUB_TOKEN. No additional setup required!

Images will be available at: `ghcr.io/anselmoo/mcp-server-analyzer`

## 🚀 Activating the Pipeline

### Step 1: Enable Workflows

1. **Rename** the current workflow file:

   ```bash
   mv .github/workflows/test-ci.yml .github/workflows/test-ci.yml.backup
   ```

2. **Activate** the full CI/CD pipeline:
   ```bash
   # The ci-cd.yml workflow is already created and ready to use
   git add .github/workflows/ci-cd.yml
   git commit -m "feat: add comprehensive CI/CD pipeline"
   git push origin main
   ```

### Step 2: Test the Pipeline

1. **Push to main branch** - triggers testing + TestPyPI + Docker build
2. **Create a version tag** - triggers full release pipeline:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

## 📊 Pipeline Workflow

### On Push to Main Branch:

- ✅ **Test & Quality**: Pre-commit hooks, pytest, multi-Python testing
- ✅ **Build Python Package**: Create distribution packages
- ✅ **Build Docker Image**: Multi-arch build + container signing
- ✅ **Publish to TestPyPI**: Test package publishing

### On Version Tag (v*.*.\*):

- ✅ **All main branch steps** +
- ✅ **Publish to PyPI**: Production package release
- ✅ **GitHub Release**: Create release with signed artifacts
- ✅ **Rerun-safe Release Assets**: Existing assets are deleted and replaced on reruns so releases stay in sync
- ✅ **Docker Latest Tag**: Update latest container image

## 🔍 Monitoring & Debugging

### GitHub Actions Dashboard

Monitor pipeline status at: `https://github.com/anselmoo/mcp-server-analyzer/actions`

### Common Issues & Solutions

#### 1. **PyPI Trusted Publishing Failed**

```
Error: Failed to authenticate with PyPI
```

**Solution**: Verify trusted publisher configuration matches exactly:

- Repository name: `mcp-server-analyzer`
- Workflow name: `ci-cd.yml`
- Environment name: `pypi`

#### 2. **Docker Build Failed**

```
Error: buildx failed with: ERROR: failed to solve
```

**Solution**: Check Dockerfile and ensure all files exist:

- `uv.lock` file present
- `pyproject.toml` configured correctly
- Source code in `src/` directory

#### 3. **Tests Failed**

```
Error: PYTHONPATH issue or missing dependencies
```

**Solution**: Ensure project structure:

- Source code in `src/mcp_python_analyzer/`
- Tests in `tests/` directory
- `PYTHONPATH=src` environment variable set

### Debug Commands

Test locally before pushing:

```bash
# Test pre-commit
uv tool run pre-commit run --all-files

# Test pytest
PYTHONPATH=src uv run pytest tests/ -v

# Test Docker build
docker build -t mcp-server-analyzer-test .

# Test package build
uv build

# Test package installation
pip install dist/*.whl
```

## 🔒 Security Best Practices

- ✅ **Trusted Publishing**: No API tokens stored in secrets
- ✅ **Container Signing**: All images signed with Cosign
- ✅ **Artifact Signing**: All releases signed with Sigstore
- ✅ **Multi-arch Support**: linux/amd64 and linux/arm64
- ✅ **Minimal Permissions**: Each job uses least-privilege access

## 📈 Release Process

### Semantic Versioning

Use semantic versioning for releases:

- **v1.0.0** - Major release
- **v1.1.0** - Minor release (new features)
- **v1.0.1** - Patch release (bug fixes)

### Release Checklist

1. ✅ Update version in `pyproject.toml`
2. ✅ Update `CHANGELOG.md`
3. ✅ Run tests locally: `uv run pytest`
4. ✅ Create version tag: `git tag v1.0.0`
5. ✅ Push tag: `git push origin v1.0.0`
6. ✅ Monitor GitHub Actions
7. ✅ Verify PyPI release
8. ✅ Test Docker image
9. ✅ Announce release

If you rerun the release workflow for the same tag, the existing GitHub Release assets are
removed and uploaded again so the published release always matches the latest build outputs.

## 🎯 Next Steps

After setting up CI/CD:

1. **Configure branch protection** for `main` branch
2. **Set up Codecov** for coverage reporting
3. **Add dependabot** for dependency updates
4. **Configure GitHub Security Advisories**
5. **Set up project documentation** with GitHub Pages

---

**🚀 Your CI/CD pipeline is now ready for production!**
