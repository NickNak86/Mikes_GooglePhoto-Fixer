# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them responsibly:

### 1. Private Reporting

Use GitHub's private vulnerability reporting feature:

1. Go to the [Security tab](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/security)
2. Click "Report a vulnerability"
3. Fill in the details

### 2. What to Include

Please include as much of the following information as possible:

- **Type of vulnerability** (e.g., SQL injection, XSS, path traversal)
- **Full paths** of source file(s) related to the vulnerability
- **Location** of the affected source code (tag/branch/commit/direct URL)
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if possible)
- **Impact** of the vulnerability
- **Potential mitigations** you're aware of

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - **Critical**: Within 7 days
  - **High**: Within 30 days
  - **Medium**: Within 90 days
  - **Low**: Next regular release

## Security Best Practices for Users

### Installation Security

1. **Verify Downloads**
   ```bash
   # Verify GitHub releases are from official repository
   # Check signatures when available
   ```

2. **Use Virtual Environments**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Keep Dependencies Updated**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

### Data Security

1. **Local Processing**
   - All photo processing happens locally
   - No data is sent to external servers
   - Your photos stay on your device

2. **File Permissions**
   - App only requests necessary permissions
   - On Android: READ/WRITE_EXTERNAL_STORAGE
   - No network access for core functionality

3. **Sensitive Data**
   - Do not commit config files with personal paths
   - Use `.gitignore` to exclude personal data
   - Review settings before sharing screenshots

### Mobile Security (Android)

1. **Permissions**
   - Only grant permissions when prompted
   - Review what permissions are requested
   - Revoke unused permissions in settings

2. **APK Verification**
   - Only install APKs from official releases
   - Verify SHA256 checksums
   - Enable "Verify apps" in Android settings

3. **Storage**
   - Store photos in app-specific directories
   - Use scoped storage (Android 10+)
   - Enable encryption if available

## Known Security Considerations

### 1. ExifTool Execution

The app uses ExifTool to read metadata. Security considerations:

- **Risk**: Command injection if paths are not sanitized
- **Mitigation**: All file paths are validated and sanitized
- **Best Practice**: Keep ExifTool updated

### 2. File System Access

The app needs broad file system access:

- **Risk**: Potential access to sensitive files
- **Mitigation**: App only processes specified directories
- **Best Practice**: Review base_path configuration

### 3. Pickle/JSON Deserialization

Config files use JSON (not pickle):

- **Risk**: Malicious config files could cause issues
- **Mitigation**: JSON is safer than pickle
- **Best Practice**: Don't load untrusted config files

### 4. OpenCV Image Processing

OpenCV processes untrusted images:

- **Risk**: Malformed images could trigger vulnerabilities
- **Mitigation**: Use latest OpenCV version
- **Best Practice**: Keep opencv-python updated

## Vulnerability Disclosure Policy

We follow coordinated disclosure:

1. **Reporter contacts us** privately
2. **We acknowledge** within 48 hours
3. **We investigate** and develop fix
4. **We notify reporter** when fix is ready
5. **We release fix** publicly
6. **We credit reporter** (if desired)

## Security Updates

Security updates are announced:

- In [CHANGELOG.md](CHANGELOG.md) with 🔒 emoji
- On [GitHub Releases](https://github.com/NickNak86/Mikes_GooglePhoto-Fixer/releases)
- With security advisory (for critical issues)

## Security-Related Configuration

### Recommended Settings

```python
# config.json
{
    "base_path": "~/PhotoLibrary",  # Use user directory
    "exiftool_path": "exiftool",    # Use system PATH
    "max_workers": 4                # Limit resource usage
}
```

### Secure File Permissions

```bash
# Recommended file permissions
chmod 700 ~/PhotoLibrary          # Owner only
chmod 600 config.json             # Owner read/write only
```

## Third-Party Dependencies

We regularly update dependencies for security:

| Dependency | Purpose | Security Notes |
|------------|---------|----------------|
| Pillow | Image processing | Keep updated, handles untrusted images |
| OpenCV | Computer vision | Keep updated, processes images |
| Kivy/KivyMD | Mobile UI | Regular updates for mobile security |
| pyjnius | Android Java bridge | Android-specific |

### Dependency Updates

```bash
# Check for security updates
pip list --outdated

# Update all dependencies
pip install --upgrade -r requirements.txt

# Check for known vulnerabilities
pip-audit  # Install: pip install pip-audit
```

## Secure Development Practices

Contributors should:

1. **Never commit secrets** (API keys, passwords, etc.)
2. **Validate all inputs** (file paths, user input)
3. **Use parameterized commands** (avoid shell injection)
4. **Keep dependencies updated**
5. **Follow least privilege** (minimal permissions)
6. **Sanitize file paths** (prevent path traversal)
7. **Handle errors securely** (no sensitive info in errors)

## Security Tools

Recommended tools for contributors:

```bash
# Static analysis
pip install bandit
bandit -r .

# Dependency security
pip install safety
safety check

# Secret scanning
pip install detect-secrets
detect-secrets scan
```

## Contact

For security concerns:
- 🔒 Use GitHub private vulnerability reporting
- 📧 Or open a private security advisory

**Please allow up to 48 hours for initial response.**

---

**Last Updated**: 2025-11-20

Thank you for helping keep Google Photos Manager secure! 🔒
