# Release Guide for Actions Advisor

This document explains how to create releases and manage tags for Actions Advisor.

## 🔄 When CI Runs

### Automatic CI Triggers

The **CI workflow** (`.github/workflows/ci.yml`) runs on:
- ✅ Every push to `main` branch
- ✅ Every pull request to `main` branch
- ❌ **NOT** triggered by tags

The **Release workflow** (`.github/workflows/release.yml`) runs on:
- ✅ When you push a tag starting with `v*` (e.g., `v1.0.0`, `v0.1.0-beta`)
- ❌ **NOT** triggered by regular commits

**Important:** You do NOT need to change tags to trigger CI. CI runs automatically on every commit to `main`.

---

## 📦 Release Process

### Step 1: Testing Release (Beta/RC)

Before creating a production release, test with a beta tag:

```bash
# Create a test tag
git tag v0.1.0-beta

# Push the tag (this triggers the release workflow)
git push origin v0.1.0-beta
```

**What happens:**
1. Release workflow builds Docker image
2. Pushes to `ghcr.io/ratibor78/actions-advisor:v0.1.0-beta`
3. Creates a GitHub Release (marked as pre-release)
4. You can test the action with `uses: ratibor78/actions-advisor@v0.1.0-beta`

### Step 2: Verify the Test Release

Check that everything works:
1. ✅ **Actions tab** - Release workflow succeeded
2. ✅ **Packages** - Docker image published to ghcr.io
3. ✅ **Releases** - GitHub release created
4. ✅ **Test in real workflow** - Try using the action

### Step 3: Production Release

Once testing is complete:

```bash
# Create production release tag
git tag v1.0.0

# Push the tag
git push origin v1.0.0
```

**What happens:**
1. Builds and pushes Docker image with multiple tags:
   - `ghcr.io/ratibor78/actions-advisor:v1.0.0` (exact version)
   - `ghcr.io/ratibor78/actions-advisor:v1.0` (minor version)
   - `ghcr.io/ratibor78/actions-advisor:v1` (major version)
   - `ghcr.io/ratibor78/actions-advisor:latest` (latest)
2. Creates a GitHub Release with auto-generated release notes

---

## 🏷️ Tag Naming Convention

### Semantic Versioning (SemVer)

Use semantic versioning: `vMAJOR.MINOR.PATCH`

**Format:** `v1.2.3`

- **MAJOR** version: Breaking changes
- **MINOR** version: New features (backward compatible)
- **PATCH** version: Bug fixes (backward compatible)

### Pre-release Tags

For testing before official release:

- **Beta:** `v1.0.0-beta`, `v1.0.0-beta.1`, `v1.0.0-beta.2`
- **Release Candidate:** `v1.0.0-rc.1`, `v1.0.0-rc.2`
- **Alpha:** `v1.0.0-alpha` (very early testing)

### Examples

```bash
# First beta release
git tag v0.1.0-beta
git push origin v0.1.0-beta

# Second beta (with fixes)
git tag v0.1.1-beta
git push origin v0.1.1-beta

# Release candidate
git tag v1.0.0-rc.1
git push origin v1.0.0-rc.1

# Production release
git tag v1.0.0
git push origin v1.0.0

# Bug fix release
git tag v1.0.1
git push origin v1.0.1

# New feature release
git tag v1.1.0
git push origin v1.1.0

# Breaking change release
git tag v2.0.0
git push origin v2.0.0
```

---

## 🔢 Version Increment Rules

### When to Increment

**PATCH (v1.0.X):**
- Bug fixes
- Documentation updates
- Performance improvements
- No new features or breaking changes

**MINOR (v1.X.0):**
- New features (backward compatible)
- New provider support
- New configuration options (with defaults)
- Deprecations (but still working)

**MAJOR (vX.0.0):**
- Breaking API changes
- Removed features
- Changed required parameters
- Changed output format
- Requires user action to upgrade

### Example Scenarios

| Change | Old Version | New Version |
|--------|-------------|-------------|
| Fix log preprocessing bug | v1.0.0 | v1.0.1 |
| Add new LLM provider | v1.0.1 | v1.1.0 |
| Add optional config parameter | v1.1.0 | v1.2.0 |
| Remove support for old API | v1.2.0 | v2.0.0 |
| Change required input names | v2.0.0 | v3.0.0 |

---

## 🛠️ How to Create a Release

### Quick Reference

```bash
# 1. Ensure all tests pass locally
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/

# 2. Update version in pyproject.toml (optional but recommended)
# Edit pyproject.toml: version = "1.0.0"

# 3. Commit any changes
git add -A
git commit -m "Prepare for v1.0.0 release"
git push

# 4. Create and push tag
git tag v1.0.0
git push origin v1.0.0

# 5. Wait for release workflow to complete
# Check: https://github.com/ratibor78/actions-advisor/actions

# 6. Verify release
# - GitHub Releases page
# - Package published to ghcr.io
# - Test with: uses: ratibor78/actions-advisor@v1.0.0
```

---

## 🗑️ Deleting a Tag (If Needed)

If you made a mistake:

```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin --delete v1.0.0

# Recreate tag
git tag v1.0.0
git push origin v1.0.0
```

**Note:** Deleting a tag after release is not recommended. Instead, create a new patch version.

---

## 📝 Release Checklist

Before creating a production release:

- [ ] All tests passing (`uv run pytest`)
- [ ] Linting passing (`uv run ruff check`)
- [ ] Type checking passing (`uv run mypy src/`)
- [ ] CI workflow passing on main branch
- [ ] Beta/RC testing completed (if applicable)
- [ ] Documentation updated (README.md)
- [ ] CHANGELOG updated (if you maintain one)
- [ ] Version bumped in pyproject.toml (optional)

---

## 🎯 Quick Commands

```bash
# See all tags
git tag

# See latest tag
git describe --tags --abbrev=0

# See commits since last tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline

# Create annotated tag with message
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push specific tag
git push origin v1.0.0

# Push all tags (not recommended)
git push origin --tags
```

---

## 🔍 Troubleshooting

### Release workflow didn't trigger
- ✅ Check tag starts with `v` (e.g., `v1.0.0` not `1.0.0`)
- ✅ Verify tag was pushed: `git ls-remote --tags origin`
- ✅ Check Actions tab for workflow runs

### Docker image not published
- ✅ Check workflow logs in Actions tab
- ✅ Verify repository permissions: Settings → Actions → Workflow permissions
- ✅ Must be "Read and write permissions"

### Can't push to ghcr.io
- ✅ Package settings → Visibility (public/private)
- ✅ Check workflow has `packages: write` permission

---

## 📚 Additional Resources

- [Semantic Versioning](https://semver.org/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
