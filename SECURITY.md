# Security Guide for OpenClaw Pro

## 🔐 Security Features

OpenClaw Pro includes comprehensive security features to protect your system and sensitive data:

### ✅ Secure Token Management
- Environment variable-based configuration
- `.env` file support (never committed to git)
- Automatic token validation
- Secure Discord bot token handling

### ✅ Command Safety
- Restricted command filtering
- Dangerous command warnings
- User confirmation for risky operations
- Blacklist for destructive commands (`rm -rf`, `dd`, etc.)

### ✅ File System Protection
- Path validation and sanitization
- System directory protection
- File size limits
- Working directory enforcement

### ✅ Web Safety
- URL validation and sanitization
- Blocked dangerous URL schemes
- HTTPS enforcement for production

## 🚀 Quick Setup

### 1. Initial Setup

```bash
# Run security setup (interactive)
python security_config.py

# Or manually create .env file
cp .env.example .env
nano .env  # Edit with your values
```

### 2. Configure .env File

```bash
# Discord Bot Token (get from discord.com/developers)
DISCORD_BOT_TOKEN=your_bot_token_here

# Ollama Settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b

# Security Settings
MAX_FILE_SIZE_MB=10
ALLOWED_DIRECTORIES=.
RESTRICTED_COMMANDS=rm -rf,dd,mkfs,format

# Business Settings
DEFAULT_BUSINESS_PLAN_DIR=./business_plans
AUTO_SAVE_RESEARCH=true
```

### 3. Verify Setup

```bash
# Check that .env is in .gitignore
cat .gitignore | grep .env

# Test OpenClaw Pro
python openclaw_pro.py --help
```

## 🔒 Best Practices

### Discord Bot Token Security

**✅ DO:**
- Store token in `.env` file
- Use environment variables
- Regenerate token if exposed
- Limit bot permissions to minimum needed
- Enable "Message Content Intent" only if needed

**❌ DON'T:**
- Commit tokens to git
- Share tokens in chat/email
- Use tokens in screenshots
- Hardcode tokens in code
- Use production tokens for testing

### Getting Discord Bot Token

1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Go to "Bot" section
4. Click "Reset Token" (or "Copy" for new bots)
5. **IMMEDIATELY** save to `.env` file
6. Enable required intents:
   - Server Members Intent (if needed)
   - Message Content Intent (required)

### File System Security

**Protected Directories:**
```bash
# These are BLOCKED by default:
/etc, /sys, /proc, /dev, /boot, /root

# Access only allowed within:
- Current working directory
- Explicitly allowed directories in config
```

**Safe Usage:**
```bash
# Work in project directories
cd ~/projects/my-project
python openclaw_pro.py

# Use git for version control
git init
git add .
git commit -m "Before AI changes"

# Run OpenClaw Pro
# Review changes
git diff

# Rollback if needed
git reset --hard
```

### Command Safety

**Blocked Commands:**
- `rm -rf` (recursive deletion)
- `dd` (disk operations)
- `mkfs` (format filesystem)
- `format` (Windows format)

**Warned Commands** (require confirmation):
- `rm -rf /` (root deletion)
- `dd if=` (disk writing)
- `chmod 777` (unsafe permissions)
- `sudo rm` (privileged deletion)
- Operations on `/dev/` devices

**Safe Commands:**
- `git` operations
- `npm`/`pip` installs
- `pytest` tests
- Application builds
- Code linting

## 🛠️ Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DISCORD_BOT_TOKEN` | Discord bot token | None | For Discord bot |
| `OLLAMA_BASE_URL` | Ollama API URL | localhost:11434 | No |
| `OLLAMA_MODEL` | Default model | qwen2.5-coder:7b | No |
| `MAX_FILE_SIZE_MB` | Max file size | 10 | No |
| `ALLOWED_DIRECTORIES` | Allowed paths | `.` (current) | No |
| `RESTRICTED_COMMANDS` | Blocked commands | See above | No |

### Customizing Security

**Add Allowed Directories:**
```bash
# In .env
ALLOWED_DIRECTORIES=.,/home/user/projects,/var/www
```

**Add Restricted Commands:**
```bash
# In .env
RESTRICTED_COMMANDS=rm -rf,dd,mkfs,format,curl | bash
```

**Increase File Size Limit:**
```bash
# In .env
MAX_FILE_SIZE_MB=50
```

## 🚨 Incident Response

### If Token is Exposed

1. **Immediately Regenerate:**
   ```
   Discord Developer Portal → Your App → Bot → Reset Token
   ```

2. **Update .env:**
   ```bash
   # Update with new token
   nano .env
   ```

3. **Check Git History:**
   ```bash
   # Check if token was committed
   git log -S "your-old-token"

   # If found, consider these sensitive  # If found, filter history (CAREFUL!)
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   ```

4. **Revoke Old Token:**
   - Old Discord tokens auto-revoked when reset
   - Monitor Discord for unauthorized usage

### If Malicious Code Executed

1. **Stop OpenClaw:**
   ```bash
   # Kill all Python processes
   pkill -f openclaw_pro.py
   ```

2. **Review Changes:**
   ```bash
   # Check git diff
   git status
   git diff

   # Check recent file modifications
   find . -type f -mmin -60  # Last 60 minutes
   ```

3. **Rollback:**
   ```bash
   # Revert to last good commit
   git reset --hard HEAD^

   # Or restore specific files
   git checkout HEAD -- file.py
   ```

4. **Audit Logs:**
   ```bash
   # Check command history
   history | grep -E "rm|dd|curl|wget"

   # Check system logs
   sudo journalctl -xe
   ```

## 📋 Security Checklist

### Before Running OpenClaw Pro

- [ ] `.env` file created and configured
- [ ] `.env` is in `.gitignore`
- [ ] Working in safe directory
- [ ] Git repository initialized
- [ ] Latest commit is clean backup
- [ ] Ollama service running
- [ ] Model downloaded

### For Discord Bot

- [ ] Bot token in `.env` (not hardcoded)
- [ ] Bot permissions minimized
- [ ] Bot not in sensitive servers
- [ ] Message content intent enabled only if needed
- [ ] Bot status monitoring enabled

### During Development

- [ ] Review AI-generated code before running
- [ ] Check file paths before operations
- [ ] Verify commands before execution
- [ ] Monitor git changes regularly
- [ ] Commit frequently
- [ ] Never use on production servers

### After Development

- [ ] Review all changes with `git diff`
- [ ] Test code in safe environment
- [ ] Remove debug/temp files
- [ ] Check for hardcoded secrets
- [ ] Update documentation
- [ ] Create clean commit

## 🔧 Advanced Security

### Running in Docker (Recommended for Production)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY openclaw_pro.py security_config.py ./

# Non-root user
RUN useradd -m openclaw
USER openclaw

# Environment variables (set via docker run)
ENV PYTHONUNBUFFERED=1

CMD ["python", "openclaw_pro.py"]
```

```bash
# Build
docker build -t openclaw-pro .

# Run (pass .env securely)
docker run --env-file .env -v $(pwd):/workspace openclaw-pro
```

### Using Secrets Manager

Instead of `.env` files, use cloud secrets:

```python
# Example: AWS Secrets Manager
import boto3
import json

def get_secret():
    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(SecretId='openclaw-pro')
    return json.loads(secret['SecretString'])

# In openclaw_pro.py
secrets = get_secret()
DISCORD_TOKEN = secrets['discord_token']
```

### Network Isolation

```bash
# Run without network (except localhost)
docker run --network none \
  -v /var/run/ollama.sock:/var/run/ollama.sock \
  openclaw-pro
```

### Audit Logging

```python
# Add to security_config.py
import logging

logging.basicConfig(
    filename='openclaw_audit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Log all tool executions
def log_tool_use(tool_name, params, user):
    logging.info(f"Tool: {tool_name} | User: {user} | Params: {params}")
```

## 📚 References

### Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Discord Bot Security](https://discord.com/developers/docs/topics/oauth2#bot-authorization-flow)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Git Security](https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage)

### Getting Help

- **Security Issue?** Email: security@example.com (or file private GitHub issue)
- **Questions?** GitHub Discussions
- **Bug Report?** GitHub Issues

## 🎓 Summary

OpenClaw Pro security features:

✅ **Token Management** - Secure `.env` file handling
✅ **Command Filtering** - Block dangerous operations
✅ **Path Validation** - Protect system directories
✅ **File Size Limits** - Prevent resource exhaustion
✅ **URL Sanitization** - Block malicious URLs
✅ **Audit Logging** - Track all operations (optional)

**Remember:**
- Never commit `.env` to git
- Review AI-generated code before running
- Use git for version control
- Run in isolated environments for production
- Keep dependencies updated

Stay secure! 🔒🦅
