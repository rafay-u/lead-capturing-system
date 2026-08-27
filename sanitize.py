
import re, sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = f.read()

# === SENSITIVE DATA REPLACEMENTS ===

# API Keys (hardcoded values)
replacements = {
    "80bd1395b700487db48ec06c40f69649": "YOUR_GEOAPIFY_API_KEY_HERE",
    "4515d9ff-0d91-4ebb-86fd-83057918760b": "YOUR_VAPI_API_TOKEN_HERE",
    "41ab521b-8297-4586-ac3c-85b2654ccbde": "YOUR_VAPI_PHONE_NUMBER_ID_HERE",
    
    # n8n Credential IDs
    "lB52MbcMWeIXFzBN": "YOUR_AIRTABLE_CREDENTIAL_ID_HERE",
    "4EH508Va1e3GQgKA": "YOUR_GMAIL_CREDENTIAL_ID_HERE",
    "ajwwjfssqii4LNHr": "YOUR_GROQ_CREDENTIAL_ID_HERE",
    "87tQME6J2wnf1WFm": "YOUR_TAVILY_CREDENTIAL_ID_HERE",
    "QqS8e9SfOvB5Jqs9": "YOUR_PERPLEXITY_CREDENTIAL_ID_HERE",
    "5xNJEYJRB74nlhuX": "YOUR_MISTRAL_CREDENTIAL_ID_HERE",
    
    # Phone numbers
    "+1 934-245-7148": "+1 XXX-XXX-XXXX",
    "+923001234567": "+XX XXX-XXXXXXX",
    
    # Instance/Workflow IDs
    "38e35f9fc1e1b8c5a545f87c905dbd7473eb93047aa8335c769e96432b28d30a": "YOUR_INSTANCE_ID_HERE",
}

for old, new in replacements.items():
    data = data.replace(old, new)

# Remove any credential name references that are account-specific
data = data.replace("Groq account 3", "YOUR_GROQ_ACCOUNT_NAME")
data = data.replace("Airtable Personal Access Token account", "YOUR_AIRTABLE_ACCOUNT_NAME")
data = data.replace("Gmail account", "YOUR_GMAIL_ACCOUNT_NAME")
data = data.replace("Tavily account", "YOUR_TAVILY_ACCOUNT_NAME")
data = data.replace("Perplexity account", "YOUR_PERPLEXITY_ACCOUNT_NAME")
data = data.replace("Mistral Cloud account", "YOUR_MISTRAL_ACCOUNT_NAME")

# Verify no secrets remain
leaked = []
for key in replacements:
    if key in data:
        leaked.append(key)

if leaked:
    print(f"WARNING: Still contains: {leaked}")
    sys.exit(1)

# Check for any remaining hex strings that look like API keys (32+ hex chars)
hex_matches = re.findall(r'[a-f0-9]{32,}', data)
if hex_matches:
    print(f"WARNING: Potential remaining tokens: {hex_matches[:3]}")
else:
    print("CLEAN: No remaining API key patterns found")

with open(sys.argv[2], 'w', encoding='utf-8') as f:
    f.write(data)

print(f"Sanitized: {sys.argv[1]} -> {sys.argv[2]}")
print(f"Original: {len(open(sys.argv[1]).read())} bytes -> Cleaned: {len(data)} bytes")
