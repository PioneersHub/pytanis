# Release Instructions for v0.9.0

## Summary of Changes Since v0.8.1

This is a minor release that includes significant improvements to the Pretalx API client:

1. **Backward Compatibility Layer**: Transparent handling of Pretalx API changes
2. **Cache Optimization**: 50-75x performance improvement for bulk operations  
3. **Integration Testing**: Comprehensive test suite for API validation
4. **Storage Abstraction**: Flexible storage backend support (from 0.8.0)

## Recent Commits (in this branch)

```
66557d5 fix: remove CLAUDE.md that should not be committed
e4547f5 docs: update documentation for testing and API changes
b316944 build: add integration test scripts and update dependencies
8f832bb fix(storage): remove circular import in Google storage adapter
e3e97e8 test: update tests for API changes and backward compatibility
b50dff8 test(pretalx): add comprehensive integration testing framework
431e904 feat(pretalx): add cache optimization for backward compatibility
5ce5cd0 feat(pretalx): add backward compatibility layer for new API changes
```

## Pre-release Checklist

- [ ] All tests passing: `hatch run cov`
- [ ] Integration tests validated: `hatch run integration`
- [ ] Documentation updated
- [ ] CHANGELOG.md updated with v0.9.0 changes
- [ ] No sensitive information in commits

## Release Commands

```bash
# 1. Ensure you're on the main branch with all changes merged
git checkout main
git pull origin main
git merge pretalx_api_update_ah

# 2. Run final tests
hatch run cov
hatch run lint:all

# 3. Update CHANGELOG.md with the v0.9.0 section

# 4. Commit the changelog
git add CHANGELOG.md
git commit -m "docs: update CHANGELOG for v0.9.0 release"

# 5. Create and push the tag
git tag -a v0.9.0 -m "Release v0.9.0: Pretalx API compatibility and performance improvements"
git push origin main
git push origin v0.9.0

# 6. Create GitHub release
# - Go to https://github.com/PyCon-DE/pytanis/releases/new
# - Select the v0.9.0 tag
# - Use the CHANGELOG content for the release notes
# - Publish the release

# 7. Build and publish to PyPI (if you have permissions)
hatch build
hatch publish
```

## Post-release

- [ ] Verify the package on PyPI
- [ ] Update any dependent projects
- [ ] Announce the release