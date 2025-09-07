# Git Commit & Push Checklist

## Pre-Commit Checklist

### 1. Review Your Changes
- [ ] **Check what files have been modified**
  ```bash
  git status
  ```

- [ ] **Review the changes in each file**
  ```bash
  git diff
  ```

- [ ] **Verify no sensitive data is included**
  - No passwords, API keys, or tokens
  - No personal information
  - No database credentials

### 2. Test Your Changes
- [ ] **Run any relevant tests**
  ```bash
  python -m pytest tests/
  ```

- [ ] **Check for syntax errors**
  ```bash
  python -m py_compile your_file.py
  ```

- [ ] **Verify functionality works as expected**

### 3. Code Quality Check
- [ ] **Follow project coding standards**
- [ ] **Add comments for complex logic**
- [ ] **Remove debug print statements**
- [ ] **Clean up temporary files**

## Commit Process

### 1. Stage Your Changes
```bash
# Stage specific files
git add filename.py

# Stage all modified files
git add .

# Stage all changes (including deletions)
git add -A
```

### 2. Write a Good Commit Message
**Format**: `type: brief description`

**Examples**:
- `fix: resolve TRIMP calculation parameter mismatch`
- `feat: add enhanced logging for admin panel comparison`
- `docs: update database schema verification process`
- `refactor: simplify database connection logic`

**Good commit message guidelines**:
- Start with a verb in present tense
- Keep first line under 50 characters
- Be specific about what changed
- Explain why if not obvious

### 3. Commit Your Changes
```bash
git commit -m "your commit message here"
```

## Push Process

### 1. Check Current Branch
```bash
git branch
```

### 2. Pull Latest Changes (if working with others)
```bash
git pull origin main
```

### 3. Push Your Changes
```bash
# Push to current branch
git push

# Push to specific branch
git push origin branch-name

# Push and set upstream (first time)
git push -u origin branch-name
```

## Common Scenarios

### Scenario 1: First Time Setup
```bash
# Clone repository
git clone <repository-url>
cd repository-name

# Create and switch to new branch
git checkout -b feature/your-feature-name

# Make your changes, then:
git add .
git commit -m "feat: add your feature description"
git push -u origin feature/your-feature-name
```

### Scenario 2: Working on Existing Branch
```bash
# Switch to your branch
git checkout your-branch-name

# Pull latest changes
git pull origin your-branch-name

# Make your changes, then:
git add .
git commit -m "fix: describe your fix"
git push
```

### Scenario 3: Multiple Commits
```bash
# Make changes to file1
git add file1.py
git commit -m "fix: resolve issue in file1"

# Make changes to file2
git add file2.py
git commit -m "feat: add new feature to file2"

# Push all commits
git push
```

### Scenario 4: Amending Last Commit
```bash
# Make additional changes
git add .
git commit --amend -m "updated commit message"

# Force push (use carefully)
git push --force-with-lease
```

## Emergency Procedures

### Undo Last Commit (before push)
```bash
git reset --soft HEAD~1
```

### Undo Last Commit (after push)
```bash
git revert HEAD
git push
```

### Discard All Local Changes
```bash
git checkout -- .
```

### Reset to Last Commit
```bash
git reset --hard HEAD
```

## Branch Management

### Create New Branch
```bash
git checkout -b feature/new-feature-name
```

### Switch Between Branches
```bash
git checkout main
git checkout your-branch-name
```

### Merge Branch
```bash
git checkout main
git merge your-branch-name
git push
```

### Delete Branch
```bash
# Delete local branch
git branch -d branch-name

# Delete remote branch
git push origin --delete branch-name
```

## Best Practices

### Do's ✅
- **Commit often** with small, logical changes
- **Write clear commit messages**
- **Test before committing**
- **Pull before pushing** when working with others
- **Use meaningful branch names**
- **Review changes with `git diff`**

### Don'ts ❌
- **Don't commit sensitive data**
- **Don't commit large binary files**
- **Don't commit debug code**
- **Don't force push to shared branches**
- **Don't commit without testing**
- **Don't use vague commit messages**

## Quick Reference Commands

| Action | Command |
|--------|---------|
| Check status | `git status` |
| See changes | `git diff` |
| Stage file | `git add filename` |
| Stage all | `git add .` |
| Commit | `git commit -m "message"` |
| Push | `git push` |
| Pull | `git pull` |
| Create branch | `git checkout -b branch-name` |
| Switch branch | `git checkout branch-name` |
| See branches | `git branch` |
| See history | `git log --oneline` |

## Troubleshooting

### "Your branch is ahead of origin"
```bash
git push
```

### "Your branch is behind origin"
```bash
git pull
```

### "Merge conflict"
```bash
# Edit conflicted files
# Remove conflict markers
git add .
git commit -m "resolve merge conflict"
```

### "Permission denied"
- Check SSH keys are set up
- Verify repository access
- Contact repository administrator

---

**Remember**: When in doubt, ask for help before making changes that could affect others!
