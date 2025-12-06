# CI/CD Setup for GooglePhoto-Fixer

## What This Does

GitHub Actions now automatically:
1. **Runs on every push/PR** to `main` or `develop` branches
2. **Validates Python syntax** for all `.py` files
3. **Runs your tests** (if you add them later)
4. **Scans for security issues** with Snyk
5. **Saves logs and results** for debugging

## Setup Steps

### 1. Add Snyk Token (Required for Security Scanning)
1. Go to https://app.snyk.io/account
2. Copy your API token
3. In GitHub: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
4. Name: `SNYK_TOKEN`, Value: (paste your token)

### 2. Commit and Push
```powershell
cd "D:\FamilyArchive"
git add .github/workflows/ci.yml
git commit -m "[CI] Add GitHub Actions workflow for automated testing"
git push
```

### 3. View Results
- Go to your GitHub repo → `Actions` tab
- You'll see a workflow run for every commit
- Green check = all passed, Red X = something failed

## Benefits

✅ **Catches errors before you do** - No more manual testing loops  
✅ **Security scanning** - Snyk finds vulnerabilities automatically  
✅ **Fast feedback** - Know within minutes if your code works  
✅ **No local setup needed** - Runs in GitHub's cloud  
✅ **History tracking** - See what broke and when  

## Next Steps

1. **Add tests**: Create `tests/` folder with pytest tests
2. **Add requirements.txt**: List your Python dependencies
3. **Customize workflow**: Add deployment, notifications, etc.

## Cost

- **Free** for public repos
- **Free** 2000 minutes/month for private repos (plenty for this project)

## Troubleshooting

If the workflow fails:
1. Click the red X in GitHub Actions
2. Click the failed job
3. Read the error message
4. Fix and commit again

**This eliminates the manual test cycle you've been stuck in!**
