# Admin Panel Documentation

The Aura admin panel allows you to view statistics, preview conversations, and download all conversations in anonymous format.

## Access

1. Navigate to `/admin` on your deployed application
2. Enter your admin key (set via `ADMIN_KEY` environment variable)
3. Click "Login"

**Security Note:** 
- If `ADMIN_KEY` is not set, admin access is allowed (development only)
- **Always set `ADMIN_KEY` in production!**

## Features

### 📊 Statistics Dashboard

View real-time statistics:
- **Total Sessions**: Number of conversation sessions
- **Total Messages**: Total messages across all sessions
- **User Messages**: Count of user messages
- **AI Messages**: Count of assistant/AI messages

Click "🔄 Refresh Stats" to update statistics.

### 📥 Download Conversations

Download all conversations in two formats:

#### CSV Format
- Click "Download CSV" to export conversations as a CSV file
- Columns: Session ID (Anonymized), Message Number, Role, Content, Timestamp
- Filename: `aura_conversations_YYYYMMDD_HHMMSS.csv`

#### JSON Format
- Click "Download JSON" to export conversations as a JSON file
- Includes metadata: export timestamp, total conversations count
- Filename: `aura_conversations_YYYYMMDD_HHMMSS.json`

### 📋 Conversations Preview

- Click "Load Conversations" to view all conversations in the browser
- See anonymized session IDs and message counts
- Preview individual messages with timestamps

## Anonymous Export

All exported data is **anonymized**:
- Session IDs are hashed (first 16 characters of hash)
- No personally identifiable information is included
- Only message content, roles, and timestamps are exported

## API Endpoints

All admin endpoints require an `admin_key` query parameter:

### Get Statistics
```
GET /api/admin/stats?admin_key=YOUR_KEY
```

### Get All Conversations
```
GET /api/admin/conversations?admin_key=YOUR_KEY
```

### Download CSV
```
GET /api/admin/download/csv?admin_key=YOUR_KEY
```

### Download JSON
```
GET /api/admin/download/json?admin_key=YOUR_KEY
```

## Setup

### Local Development

1. Add `ADMIN_KEY` to your `.env` file:
```env
ADMIN_KEY=your_secure_key_here
```

2. Generate a secure key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

3. Restart your application

### Production (Railway/Cloud)

1. Add `ADMIN_KEY` environment variable in your cloud provider dashboard
2. Use a strong, random key (at least 32 characters)
3. Redeploy your application

## Security Best Practices

1. **Always set `ADMIN_KEY` in production**
2. **Use a strong, random key** (32+ characters)
3. **Keep your admin key secret** - don't commit it to git
4. **Use HTTPS** in production to encrypt admin key transmission
5. **Limit access** - only share admin key with trusted administrators
6. **Rotate keys periodically** - change your admin key regularly

## Privacy & Compliance

- **All exported data is anonymized** - session IDs are hashed
- **No user identification** - only conversation content is exported
- **GDPR-friendly** - exports contain no personally identifiable information
- **Use responsibly** - ensure compliance with your privacy policy and regulations
