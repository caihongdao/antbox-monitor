# WORKFLOW_AUTO.md - Automated Workflow Configuration

## Purpose
Define automated workflows for common tasks, including GitHub API authentication for searching repositories and bypassing rate limits.

## GitHub Token Configuration
To use the provided GitHub token for authenticated API requests:

1. **Environment Variable**: Set `GITHUB_TOKEN` in the shell environment
2. **API Usage**: Use `curl -H "Authorization: token $GITHUB_TOKEN"` for GitHub API calls
3. **Search Rate Limits**: Authenticated requests have higher rate limits (5000 requests per hour vs 60 for unauthenticated)

## Search Workflow for DNF Mobile Emulator & Scripts
When searching for game emulators and scripts:

1. Use GitHub Search API with authenticated token
2. Search keywords in Chinese and English
3. Filter by repository topics, descriptions, and README content
4. Prioritize repositories with recent updates and active maintenance

## Token Security Notes
- **Never commit token to version control**
- **Store in environment variable or secure credential store**
- **Rotate token if exposed**
- **Use token only for read-only search operations (no write access needed)**

## Emulator Detection Bypass Research Strategy
1. Search for "Tencent emulator detection bypass" repositories
2. Look for Android emulator modification projects
3. Search for "DNF手游 模拟器 防检测" (Chinese keywords)
4. Explore Auto.js, 触动精灵 script repositories
5. Check for "毛驴3脚本" references in forums or code comments

## Automated Search Commands
```bash
# Example authenticated GitHub search
curl -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/search/repositories?q=DNF+手游+模拟器+检测&sort=updated&order=desc"
```

## Update Frequency
This file should be reviewed and updated when search strategies or authentication methods change.