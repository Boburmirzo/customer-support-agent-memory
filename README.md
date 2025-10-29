# Customer Support AI Agent with DigitalOcean's Gradient AI platform and Memori

A powerful, embeddable AI customer support solution that can be integrated into any website with a single JavaScript snippet. Built using DigitalOcean's Gradient AI platform for AI agent capabilities and Memori for persistent conversation memory.

## Features

- 🤖 **AI-Powered Support**: Uses DigitalOcean's Gradient AI platform for contextual understanding
- 🕷️ **Website Scraping**: Automatically analyzes website content for context-aware responses  
- 💾 **Persistent Storage**: Agents and knowledge bases survive application restarts
- 🗃️ **Dual Storage Pattern**: Fast memory cache with PostgreSQL fallback for reliability
- 🚀 **Easy Integration**: Single JavaScript snippet for any website
- 🐳 **Docker Ready**: Complete containerized setup with docker-compose
- 🔒 **Session Management**: Secure session handling with user tracking
- 🎨 **Customizable Widget**: Configurable appearance and behavior

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Website       │    │   FastAPI        │    │   PostgreSQL    │
│   + Widget.js   │◄──►│   Backend        │◄──►│   (Persistence) │
│                 │    │   (DigitalOcean) │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ DigitalOcean AI  │
                       │  (Gradient AI)   │
                       └──────────────────┘
```

### Data Flow
1. **Memory First**: Agents and knowledge bases cached in memory for fast access
2. **Database Fallback**: If not in memory, loads from PostgreSQL
3. **API Creation**: Creates new resources via DigitalOcean if not found
4. **Auto-Save**: All resources automatically saved to database for persistence

## Quick Start

### Prerequisites

- Docker and Docker Compose
- DigitalOcean API token with Gradient AI access
- Python 3.11+ (for local development)

### 1. Clone and Configure

```bash
git clone <repository-url>
cd customer-support-agent-memori

# Update your DigitalOcean credentials in .env file
cp .env.example .env
# Edit .env and add your DIGITALOCEAN_TOKEN and other DigitalOcean variables
```

### 2. Start with Docker

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

The API will be available at `http://localhost:8000`

### 3. Test the Integration

Open `http://localhost:8000/static/demo.html` to see the widget in action.

## Manual Setup (Development)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup PostgreSQL

```bash
# Install PostgreSQL
# On macOS with Homebrew:
brew install postgresql

# Start PostgreSQL
brew services start postgresql

# Create database and user
createdb customer_support
psql customer_support < init.sql

# For existing installations, run the migration:
psql -h localhost -U do_user -d customer_support -f migrate_db.sql
```

### 3. Configure Environment

```bash
# Copy and edit environment variables
cp .env.example .env
# Edit .env with your database and API settings
```

### 4. Run the Application

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Integration Guide

### Basic Integration

Add this to your website's HTML:

```html
<!-- Include the widget script -->
<script src="http://localhost:8000/static/widget.js"></script>

<!-- Initialize the widget -->
<script>
window.CustomerSupportWidgetConfig = {
    apiUrl: 'http://localhost:8000',
    data-domain-id: 'YOUR_GIBSONAI_MEMORI_API_KEY', // Required!
    primaryColor: '#007bff',
    widgetTitle: 'Customer Support',
    welcomeMessage: 'Hi! How can I help you today?',
    autoScrape: true
};
CustomerSupportWidget.init(window.CustomerSupportWidgetConfig);
</script>
```

### Advanced Configuration

```javascript
CustomerSupportWidget.init({
    // Required
    apiUrl: 'https://your-api-domain.com',
    apiKey: 'YOUR_GIBSONAI_MEMORI_API_KEY',
    // Appearance
    position: 'bottom-right', // 'bottom-left', 'top-right', 'top-left'
    primaryColor: '#007bff',
    secondaryColor: '#f8f9fa',
    textColor: '#333',
    
    // Content
    widgetTitle: 'Customer Support',
    welcomeMessage: 'Hi! How can I help you today?',
    placeholder: 'Type your message...',
    
    // Behavior
    autoScrape: true // Automatically scrape current website
});
```

### Widget API

```javascript
// Programmatic control
CustomerSupportWidget.open();                    // Open chat window
CustomerSupportWidget.close();                   // Close chat window
CustomerSupportWidget.sendMessage('Hello!');     // Send a message
CustomerSupportWidget.destroy();                 // Remove widget
```

## API Endpoints

### Session Management

#### Start Session
```http
POST /session
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
    "user_id": "user123",
    "website_url": "https://example.com"
}
```

### Knowledge Base Management

#### Upload File (PDF, TXT, MD, JSON, CSV)
```http
POST /knowledge/upload/file
Content-Type: multipart/form-data
Authorization: Bearer YOUR_API_KEY

Form data:
- website_url: "https://example.com"
- file: [binary file data]
- chunk_size: 1000 (optional)
- use_semantic: false (optional)
- custom_name: "Custom Document Name" (optional)

Supported file types:
- PDF (.pdf) - Extracts text from PDF documents
- Text (.txt) - Plain text files
- Markdown (.md) - Markdown documents with formatting
- JSON (.json) - Structured JSON data
- CSV (.csv) - Tabular data from CSV files
```

#### Upload Text Content
```http
POST /knowledge/upload/text
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
    "website_url": "https://example.com",
    "text_content": "Your plain text content here...",
    "document_name": "My Document",
    "chunk_size": 1000,
    "use_semantic": false
}
```

#### Upload from URL
```http
POST /knowledge/upload/url
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
    "website_url": "https://example.com",
    "url_to_scrape": "https://docs.example.com",
    "max_depth": 2,
    "max_links": 20,
    "chunk_size": 1000
}
```

#### Get Supported File Types
```http
GET /knowledge/supported-types
Authorization: Bearer YOUR_API_KEY

Response:
{
    "supported_types": [".pdf", ".txt", ".md", ".json", ".csv"],
    "descriptions": {
        ".pdf": "PDF documents",
        ".txt": "Plain text files",
        ".md": "Markdown documents",
        ".json": "JSON data files",
        ".csv": "CSV data files"
    },
    "additional_sources": ["url", "text"]
}
```

### Website Scraping (Legacy - Use /knowledge/upload/url instead)
```http
POST /scrape
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
    "website_url": "https://example.com",
    "max_pages": 10,
    "depth": 2
}
```

### Chat

#### Ask Question
```http
POST /ask
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
    "question": "How do I reset my password?",
    "session_id": "uuid-here",
    "user_id": "user123",
    "website_context": "https://example.com/login"
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DIGITALOCEAN_TOKEN` | DigitalOcean API token (required) | - |
| `DIGITALOCEAN_AGENT_NAME` | Agent name prefix | `customer-support` |
| `DIGITALOCEAN_KNOWLEDGE_BASE_NAME` | KB name prefix | `website-kb` |
| `DIGITALOCEAN_AGENT_INSTRUCTIONS` | Agent instructions | Custom instructions |
| `DIGITALOCEAN_MODEL` | AI model to use | `deepseek-ai/DeepSeek-V3` |
| `POSTGRES_HOST` | PostgreSQL host | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `POSTGRES_DB` | Database name | `customer_support` |
| `POSTGRES_USER` | Database user | `do_user` |
| `POSTGRES_PASSWORD` | Database password | `do_user_password` |

## Database Schema

The system automatically creates the following tables:

### Core Tables
- `user_sessions` - Manages user sessions with status tracking
- `agents` - Stores DigitalOcean agent metadata and access keys
- `knowledge_bases` - Tracks knowledge base UUIDs and website associations

### Agent Persistence
```sql
-- Agents table stores DigitalOcean agent information
CREATE TABLE agents (
    website_key TEXT PRIMARY KEY,
    agent_uuid TEXT NOT NULL,
    agent_url TEXT NOT NULL,
    agent_access_key TEXT,
    knowledge_base_uuids TEXT[],
    website_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Knowledge Bases table stores KB metadata
CREATE TABLE knowledge_bases (
    website_key TEXT PRIMARY KEY,
    kb_uuid TEXT NOT NULL,
    website_url TEXT NOT NULL,
    kb_name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Migration

**For existing installations**, run the migration script to add persistence tables:

```bash
psql -h localhost -U do_user -d customer_support -f migrate_db.sql
```

This adds the `agents` and `knowledge_bases` tables without affecting existing data.

### Monitoring

Check stored resources:

```sql
-- View all agents
SELECT website_key, agent_uuid, website_url, created_at 
FROM agents 
ORDER BY created_at DESC;

-- View all knowledge bases
SELECT website_key, kb_uuid, website_url, kb_name 
FROM knowledge_bases 
ORDER BY created_at DESC;

-- Count resources
SELECT 
    (SELECT COUNT(*) FROM agents) as total_agents,
    (SELECT COUNT(*) FROM knowledge_bases) as total_kbs,
    (SELECT COUNT(*) FROM user_sessions WHERE status = 'active') as active_sessions;
```

For detailed documentation on database persistence, see `DATABASE_PERSISTENCE.md`.

## Customization

### Custom Instructions

Modify the agent instructions via environment variable:

```bash
# In .env file
DIGITALOCEAN_AGENT_INSTRUCTIONS="You are a Customer Support AI Assistant for [Your Company].

[Add your custom instructions here]"
```

Or modify in `main_gradient.py`:

```python
instructions=os.getenv("DIGITALOCEAN_AGENT_INSTRUCTIONS", dedent(
    """\
    You are a Customer Support AI Assistant.
    [Your instructions here]
    """
))
```

### Custom Styling

The widget supports extensive CSS customization:

```javascript
CustomerSupportWidget.init({
    primaryColor: '#your-brand-color',
    secondaryColor: '#your-bg-color',
    // Add custom CSS
    customCSS: `
        #customer-support-widget {
            /* Your custom styles */
        }
    `
});
```

## Production Deployment

### Security Considerations

1. **API Keys**: Store DigitalOcean token securely
2. **CORS**: Configure allowed origins properly
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **SSL**: Use HTTPS in production
5. **Database**: Secure PostgreSQL with proper authentication
6. **Agent Access Keys**: Stored securely in database, encrypted at rest

### Scaling

1. **Database**: Use managed PostgreSQL service (AWS RDS, etc.)
2. **API**: Deploy behind load balancer
3. **Caching**: Implement Redis for session caching
4. **CDN**: Serve widget.js from CDN

### Monitoring

Monitor these metrics:
- API response times
- Database performance (check `agents` and `knowledge_bases` tables)
- Session creation rate
- DigitalOcean API usage and quotas
- Error rates
- Memory cache hit/miss rates

## Troubleshooting

### Common Issues

1. **Widget not appearing**
   - Check console for JavaScript errors
   - Verify API URL is correct
   - Ensure CORS is configured properly

2. **Database connection errors**
   - Verify PostgreSQL is running
   - Check DATABASE_URL format
   - Verify user permissions (do_user)
   - Run migration if tables missing: `psql -f migrate_db.sql`

3. **DigitalOcean API errors**
   - Verify DIGITALOCEAN_TOKEN is valid
   - Check account access to Gradient AI
   - Monitor API rate limits
   - Check agent and KB creation logs

4. **Persistence issues**
   - Verify `agents` and `knowledge_bases` tables exist
   - Check database logs for constraint violations
   - Monitor startup logs for "Loaded X agents/KBs"
   - Query database to verify resources saved correctly

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --log-level debug
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Code Structure

```
├── main_gradient.py     # FastAPI application with DigitalOcean integration
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker services
├── Dockerfile          # API container
├── init.sql            # Database initialization with persistence tables
├── migrate_db.sql      # Migration script for existing installations
├── .env                # Environment variables
├── DATABASE_PERSISTENCE.md  # Detailed persistence documentation
├── IMPLEMENTATION_SUMMARY.md # Quick implementation reference
├── ARCHITECTURE.md     # System architecture documentation
├── QUICK_REFERENCE.md  # API quick reference
├── static/
│   ├── widget.js       # Embeddable widget
│   └── demo.html       # Integration demo
└── README.md           # This file
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation at `/docs`