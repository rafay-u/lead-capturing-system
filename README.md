# n8n Lead Generation Automation

**B2B lead generation, research, and outreach automation workflow for n8n** — sanitized, production-ready, zero secrets.

## Overview

This repository contains a complete n8n workflow (`workflows/leads-construction-system.json`) that automates the entire B2B lead lifecycle:

```
┌─────────────────────────────────────────────────────────────────┐
│                    LEADS CONSTRUCTION SYSTEM                    │
├─────────────────────────────────────────────────────────────────┤
│  1. LEAD DISCOVERY (Manual Trigger)                            │
│     Form → Build Query → Geoapify Geocode → Geoapify Places    │
│     → Extract Top 20 → Dedupe → Airtable                       │
├─────────────────────────────────────────────────────────────────┤
│  2. DAILY RESEARCH (Scheduled 09:30)                           │
│     Get New Leads → Loop → Perplexity/Tavily → Groq/Mistral    │
│     → Parse → Save Research to Airtable                        │
├─────────────────────────────────────────────────────────────────┤
│  3. DAILY OUTREACH (Scheduled 09:30)                           │
│     Get Researched Leads → Loop → Stagger Delay →              │
│       ├─ Vapi Voice Call → Log Call                             │
│       └─ Draft Email (Groq/Mistral) → Send Gmail → Log Email   │
│     → Merge → Next Lead                                        │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- n8n instance (self-hosted or cloud)
- Accounts for all integrated services (see `.env.example`)
- `jq` installed (for import script)

### 1. Clone & Configure

```bash
git clone https://github.com/rafay-u/n8n-lead-gen-automation.git
cd n8n-lead-gen-automation
cp .env.example .env
# Edit .env with your actual API keys and credentials
```

### 2. Set Up n8n Credentials

In n8n **Settings → Credentials**, create these credential types using the templates in `configs/n8n-config.json.example`:

| Credential Type | Service | Purpose |
|-----------------|---------|---------|
| Airtable Token API | Airtable | Lead database |
| Gmail OAuth2 | Google | Email outreach |
| Groq API | Groq | LLM inference |
| Tavily API | Tavily | Web search |
| Perplexity API | Perplexity | AI research |
| Mistral Cloud API | Mistral | Alternative LLM |

### 3. Import Workflow

```bash
export N8N_URL=https://your-n8n-instance.com
export N8N_API_KEY=your-n8n-api-key
./scripts/import-workflow.sh
```

### 4. Activate Workflows

In n8n UI:
1. Open "Leads Construction System"
2. Click **Activate** on all three trigger nodes:
   - **New Lead Search** (manual form trigger)
   - **Daily Research Run** (scheduled 09:30)
   - **Daily Outreach Run** (scheduled 09:30)

## Folder Structure

```
n8n-lead-gen-automation/
├── .env.example              # Environment variable template
├── .gitignore                # Git exclusions
├── README.md                 # This file
├── raw_workflow.json         # Original unsanitized export (reference)
├── sanitize.py               # Secret scrubber script
├── workflows/
│   └── leads-construction-system.json  # Production workflow (sanitized)
├── docs/
│   └── workflow-architecture.md        # Detailed node-by-node docs
├── scripts/
│   └── import-workflow.sh              # n8n import helper
└── configs/
    └── n8n-config.json.example         # Credential setup reference
```

## Environment Variables

Copy `.env.example` → `.env` and fill in:

```bash
# Core APIs
GEOAPIFY_API_KEY=           # Geocoding + Places search
VAPI_API_TOKEN=             # Voice AI outbound calls
VAPI_PHONE_NUMBER_ID=       # Vapi phone number to call from

# Airtable (lead database)
AIRTABLE_BASE_ID=
AIRTABLE_TABLE_ID=
AIRTABLE_CREDENTIAL_ID=     # n8n credential ID

# Email
GMAIL_CREDENTIAL_ID=        # n8n credential ID

# LLM Providers
GROQ_CREDENTIAL_ID=         # n8n credential ID
TAVILY_CREDENTIAL_ID=
PERPLEXITY_CREDENTIAL_ID=
MISTRAL_CREDENTIAL_ID=

# n8n
N8N_INSTANCE_ID=
```

See `.env.example` for detailed comments and optional settings.

## Usage

### Manual Lead Search

1. In n8n, open "New Lead Search" form trigger
2. Fill the form:
   - **Industry/Niche** (required): e.g., "IT Services", "Bakery", "Gym"
   - **City** (required): e.g., "Lahore", "Karachi"
   - **Country** (default: Pakistan)
   - **Extra Keyword** (optional): e.g., "software", "artisan"
3. Submit → workflow discovers 20 places via Geoapify → stores new leads in Airtable

### Automated Daily Runs

- **09:30** Daily Research Run: Researches all "New" status leads → updates to "Researched"
- **09:30** Daily Outreach Run: Calls + emails all "Researched" leads → updates to "Contacted"

Staggered delays (15 min between calls) respect rate limits.

## Customization

### Modify Industry Categories

Edit the **Map Industry to Category** node (Code node) to add new mappings:

```javascript
const map = {
  "it service": "commercial",
  "bakery": "commercial.bakery",
  "restaurant": "catering.restaurant",
  "gym": "sport.fitness",
  "clinic": "healthcare.clinic_or_praxis",
  "salon": "service.beauty"
  // ADD YOUR MAPPINGS HERE
};
```

### Adjust Search Radius

In **Geoapify Places Search** node, change `filter` parameter:
```
circle:{lon},{lat},5000  // 5km radius
```

### Change Schedule

Modify **Daily Research Run** and **Daily Outreach Run** trigger nodes (Schedule Trigger).

## Security

- **No secrets in this repo** — all API keys, tokens, phone numbers, credential IDs, and instance IDs replaced with `YOUR_*` placeholders
- `.env` is gitignored — never commit it
- `raw_workflow.json` contains original secrets — keep local only or delete

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-improvement`
3. Make changes, test in n8n
4. Run sanitization: `python sanitize.py workflows/leads-construction-system.json workflows/leads-construction-system.json`
5. Commit with conventional messages: `git commit -m "feat: add dental clinic category mapping"`
6. Push and open PR

## License

MIT — free to use, modify, distribute.

## Support

- Issues: [GitHub Issues](https://github.com/rafay-u/n8n-lead-gen-automation/issues)
- n8n Community: [community.n8n.io](https://community.n8n.io)