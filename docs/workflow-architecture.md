# Workflow Architecture Documentation

## Leads Construction System — Node-by-Node Flow

This document describes the 38-node n8n workflow organized into three independent pipelines.

---

## Pipeline 1: Lead Discovery (Manual Form Trigger)

**Trigger:** `New Lead Search` (Form Trigger) — manual web form
**Schedule:** On-demand

### Node Flow

| # | Node | Type | Purpose |
|---|------|------|---------|
| 1 | New Lead Search | Form Trigger | Collects: Industry, City, Country, Extra Keyword |
| 2 | Build Search Query | Set | Composes `searchQuery` + extracts city/country/category |
| 3 | Geocode City | HTTP Request | Geoapify Geocode API → lat/lon for city |
| 4 | Map Industry to Category | Code | Maps free-text industry → Geoapify category code |
| 5 | Geoapify Places Search | HTTP Request | Geoapify Places API (category + 5km radius) → up to 20 places |
| 6 | Extract Top 20 Results | Code | Normalizes place data: name, phone, website, email, address, category |
| 7 | Loop Places | SplitInBatches | Iterates each place (batch size 1) |
| 8 | Check Duplicate Phone | Airtable (Search) | Checks if phone already exists in Airtable |
| 9 | Is Duplicate? | IF | Branches: duplicate → skip; new → create |
| 10 | Skip - Already In Airtable | NoOp | Pass-through for duplicates |
| 11 | Add New Lead | Airtable (Create) | Inserts new lead with Status="New" |

### Loop Back
- Both **Skip** and **Add New Lead** → `Loop Places` (next iteration)

### Key Variables Passed Through Loop
- `businessName`, `phone`, `website`, `email`, `address`, `city`, `country`, `category`, `place_id`, `sourceQuery`

### Data Source
- **Geoapify API** (requires `GEOAPIFY_API_KEY`)
- **Airtable** (requires base/table + PAT credential)

---

## Pipeline 2: Daily Research (Scheduled)

**Trigger:** `Daily Research Run` (Schedule Trigger) — 09:30 daily
**Processes:** All leads with `Status = "New"`

### Node Flow

| # | Node | Type | Purpose |
|---|------|------|---------|
| 1 | Daily Research Run | Schedule Trigger | Cron: daily 09:30 |
| 2 | Get New Leads | Airtable (Search) | Formula: `{Status}="New"` |
| 3 | Loop Leads - Research | SplitInBatches | Iterates each new lead |
| 4 | Wait Between Research Calls | Wait | 10s delay between API calls |
| 5 | Research Agent | LangChain Agent | LLM agent with Perplexity + Tavily tools |
| 6 | Parse Agent Output | Code | Extracts JSON from agent output |
| 7 | Save Research to Airtable | Airtable (Update) | Updates lead with research + Status="Researched" |

### Research Agent Tools
- **Perplexity Tool**: Summarized web info (reviews, reputation, competitors)
- **Tavily Tool**: Raw page search (LinkedIn, company site, staff pages)

### Research Agent Model Chain
- Primary: **Groq** (llama-3.3-70b-versatile)
- Fallback: **Mistral** (magistral-small-latest)

### Output Fields Saved
- `Research Summary`, `Pain Points`, `Wasted Time Manual Work`, `Competitors`, `Social Media Links`, `Reviews Summary`, `Decision Maker Name`, `Email`, `Status="Researched"`, `Date Researched`

---

## Pipeline 3: Daily Outreach (Scheduled)

**Trigger:** `Daily Outreach Run` (Schedule Trigger) — 09:30 daily
**Processes:** All leads with `Status = "Researched"`

### Node Flow

| # | Node | Type | Purpose |
|---|------|------|---------|
| 1 | Daily Outreach Run | Schedule Trigger | Cron: daily 09:30 |
| 2 | Get Researched Leads | Airtable (Search) | Formula: `{Status}="Researched"` |
| 3 | Loop Leads - Outreach | SplitInBatches | Iterates each researched lead (2 parallel branches) |

### Branch A: Voice Call (Vapi)

| # | Node | Type | Purpose |
|---|------|------|---------|
| 4a | Compute Stagger Delay | Code | Index-based delay: 0min for first, 15min for rest |
| 5a | Wait 30 Min Between Calls | Wait | Enforces stagger |
| 6a | Vapi Outbound Call | HTTP Request | POST to Vapi API with dynamic assistant config |
| 7a | Log Call Sent | Airtable (Update) | Sets `Call Status="Called"`, `Date Contacted` |

### Branch B: Email Outreach (Gmail)

| # | Node | Type | Purpose |
|---|------|------|---------|
| 4b | Draft Cold Email | LangChain LLM Chain | Generates personalized cold email (Groq primary, Mistral fallback) |
| 5b | Separation | Code | Parses JSON output from LLM |
| 6b | Loop | Code | Re-uses stagger delay logic |
| 7b | Waits | Wait | Same stagger delay |
| 8b | Send Cold Email | Gmail | Sends to lead's Email field |
| 9b | Log Email Sent | Airtable (Update) | Sets `Email Status="Sent"`, `Date Contacted` |

### Merge & Continue
| # | Node | Type | Purpose |
|---|------|------|---------|
| 10 | Merge Branches | Merge | Waits for both branches → continues loop |

### Vapi Assistant Configuration (Dynamic per Lead)
- **Model**: Groq llama-3.3-70b-versatile
- **Voice**: ElevenLabs `Q0Et7LOU7VpeoeCRQAVS`
- **System Prompt**: Includes lead-specific research summary, wasted-time task, pain points
- **First Message**: "Hi, is this [Decision Maker]? Calling about [Business Name] — got 30 seconds?"

### Email Template
- Under 180 words, professional, non-spammy
- Names specific manual task costing them time
- Pitches workflow automation as fix
- Soft CTA: 15-min call
- Footer mentions agent-driven research

---

## Shared Resources

### Airtable Schema (`tblOZT0yNsiVUy1sC` in base `appvdVbbi40H4Szps`)

Key fields:
- **Business Name**, **Phone**, **Email**, **Website**, **Address**, **City**, **Category**
- **Status**: New → Researched → Contacted → Closed
- **Research Summary**, **Pain Points**, **Wasted Time Manual Work**, **Competitors**
- **Social Media Links**, **Reviews Summary**, **Decision Maker Name**
- **Call Status**: Not Called / Called / No Answer / Voicemail / Interested / Not Interested
- **Email Status**: Not Sent / Sent / Replied
- **Source Query**, **Date Added**, **Date Researched**, **Date Contacted**

### Credentials Referenced (by n8n credential ID)
- `airtableTokenApi` — Airtable Personal Access Token
- `gmailOAuth2` — Gmail OAuth2
- `groqApi` — Groq API Key
- `tavilyApi` — Tavily API Key
- `perplexityApi` — Perplexity API Key
- `mistralCloudApi` — Mistral Cloud API Key

---

## Connections Summary

```
Pipeline 1: New Lead Search → Build Search Query → Geocode City → Map Industry → Geoapify Places → Extract → Loop Places → [Check Duplicate → Is Duplicate? → (Skip | Add New Lead)] → Loop Places

Pipeline 2: Daily Research Run → Get New Leads → Loop Leads - Research → Wait → Research Agent (Perplexity+Tavily) → Parse → Save Research → Loop Leads - Research

Pipeline 3: Daily Outreach Run → Get Researched Leads → Loop Leads - Outreach → [Branch A: Compute Stagger → Wait → Vapi Call → Log Call] + [Branch B: Draft Email → Separate → Loop → Wait → Send Email → Log Email] → Merge Branches → Loop Leads - Outreach
```

---

## Trigger Scheduling

| Trigger | Cron | Timezone |
|---------|------|----------|
| Daily Research Run | `30 9 * * *` | Server local |
| Daily Outreach Run | `30 9 * * *` | Server local |

Both run at 09:30 daily. Research completes first (typically < 30 min), then Outreach processes freshly-researched leads.

---

## Rate Limit Considerations

| Service | Limit | Mitigation |
|---------|-------|------------|
| Geoapify | 3000/day free | Single batch of 20 per manual run |
| Vapi | Account-dependent | 15-min stagger between calls |
| Gmail | 500/day (standard) | Same stagger, batched daily |
| Groq | 30 RPM free | Single-threaded via loop |
| Perplexity/Tavily | Account-dependent | Wait node + single-threaded |

---

## Extending the Workflow

### Add New Industry Category
Edit **Map Industry to Category** node:
```javascript
const map = {
  "dental clinic": "healthcare.dentist",
  "real estate": "commercial.real_estate",
  // ...
};
```

### Add New Research Field
1. Update Research Agent prompt (add field to JSON output spec)
2. Update Parse Agent Output node
3. Update Save Research to Airtable columns
4. Add field to Airtable base

### Change Outreach Channel
- Replace Vapi Call branch with Twilio, Plivo, etc.
- Replace Gmail with SendGrid, Mailgun, Outlook
- Keep Merge Branches pattern for parallel execution

---

## File Reference
- **Workflow JSON**: `workflows/leads-construction-system.json`
- **Env Template**: `.env.example`
- **Credential Config**: `configs/n8n-config.json.example`
- **Import Script**: `scripts/import-workflow.sh`