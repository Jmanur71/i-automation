# FREE AI MODELS SETUP FOR INTERVIEW COPILOT

## Quick Summary

You have **TWO FREE OPTIONS** for instant interview answers:

1. **Google Gemini** - Completely free, no credit card
2. **OpenAI GPT-3.5-turbo** - Very cheap (~$0.05 per 100 questions)

Both integrate seamlessly. Choose one and follow the setup below.

---

## Option 1: Google Gemini (RECOMMENDED - Completely Free)

### Why Gemini?
✅ Completely free (no credit card)  
✅ 1500 requests/day free quota  
✅ Super fast responses (< 500ms average)  
✅ Great for technical questions  
✅ No billing concerns  

### Setup Steps

**Step 1: Get API Key**
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click on your profile → Select a project (or create new)
3. Click **"Create API Key"**
4. Copy the key

**Step 2: Add to `.env.local`**

Create or edit `AI-powererd-interview-Assistant/.env.local`:

```env
# Google Gemini Configuration
GOOGLE_API_KEY=your_gemini_api_key_here
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-flash

# Optional: For OpenAI fallback
# OPENAI_API_KEY=your_key_here
```

**Step 3: Test Connection**

```bash
cd AI-powererd-interview-Assistant
npm run verify-setup
```

### Free Tier Limits
- **60 requests/minute** (plenty for interviews)
- **1500 requests/day** (50+ questions)
- **Request timeout**: 2 minutes
- **Free forever** (no hidden costs)

### When to Upgrade
- Need > 1500 daily requests
- Want faster processing
- Need dedicated support

---

## Option 2: OpenAI GPT-3.5-turbo (Cheap Alternative)

### Why OpenAI?
✅ More consistent performance  
✅ Better for complex reasoning  
✅ Higher rate limits (3500 req/min)  
✅ Proven reliability  
❌ Costs money (~$0.05 per 100 questions)  

### Setup Steps

**Step 1: Create OpenAI Account**
1. Go to [OpenAI Platform](https://platform.openai.com/signup)
2. Sign up with email or Google
3. Verify email
4. Add payment method

**Step 2: Get API Key**
1. Go to [API Keys](https://platform.openai.com/api/keys)
2. Click **"Create new secret key"**
3. Copy the key (only shows once!)
4. Save it somewhere safe

**Step 3: Set Up Billing (Optional)**
1. Go to [Billing](https://platform.openai.com/account/billing/overview)
2. Set up payment method
3. Optional: Set monthly budget limit for safety

**Step 4: Add to `.env.local`**

Create or edit `.env.local`:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_key_here
AI_PROVIDER=openai
OPENAI_MODEL=gpt-3.5-turbo

# Optional: For Gemini fallback
# GOOGLE_API_KEY=your_key_here
```

**Step 5: Test Connection**

```bash
cd AI-powererd-interview-Assistant
npm run verify-setup
```

### Cost Breakdown

**GPT-3.5-turbo Pricing:**
- Input: $0.0005 / 1K tokens
- Output: $0.0015 / 1K tokens

**Example Interview Session:**
- Average question: 20 tokens input, 200 tokens output
- Cost per question: ~$0.0004
- Cost per 100 questions: ~$0.04
- Cost per 10,000 questions: ~$4

---

## Detailed Setup Guide

### Environment Variables Explained

```env
# === AI Provider Selection ===
AI_PROVIDER=gemini        # Use "gemini" or "openai"

# === Google Gemini ===
GOOGLE_API_KEY=...        # Your Gemini API key
GEMINI_MODEL=gemini-1.5-flash  # Model to use

# === OpenAI ===
OPENAI_API_KEY=sk-...     # Your OpenAI API key
OPENAI_MODEL=gpt-3.5-turbo    # Model to use

# === Optional: RAG/Advanced Features ===
PINECONE_API_KEY=...      # For knowledge base (optional)
TAVILY_API_KEY=...        # For web search (optional)
```

### File Location

**Windows:**
```
C:\Users\[Username]\Downloads\Interview\AI-powererd-interview-Assistant\.env.local
```

**Mac/Linux:**
```
~/Downloads/Interview/AI-powererd-interview-Assistant/.env.local
```

### Complete `.env.local` Template

```env
# ===== AI PROVIDER SETUP =====

# Option 1: Google Gemini (Recommended - Free)
GOOGLE_API_KEY=AIzaSy...
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-flash

# Option 2: OpenAI (Cheap)
# OPENAI_API_KEY=sk-...
# AI_PROVIDER=openai
# OPENAI_MODEL=gpt-3.5-turbo

# ===== OPTIONAL: ADVANCED FEATURES =====

# For RAG (document search)
PINECONE_API_KEY=
PINECONE_INDEX_NAME=interview-copilot

# For web search
TAVILY_API_KEY=

# For Deepgram (audio transcription)
DEEPGRAM_API_KEY=

# For Claude (alternative AI)
ANTHROPIC_API_KEY=

# ===== ENVIRONMENT =====
NODE_ENV=development
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

## Verification & Testing

### Test 1: Check Environment Variables

```bash
cd AI-powererd-interview-Assistant

# Windows PowerShell:
cat .env.local | Select-String "API_KEY"

# Mac/Linux:
cat .env.local | grep API_KEY
```

Output should show your API keys (partially hidden is fine).

### Test 2: Run Verification Script

```bash
npm run verify-setup
```

Expected output:
```
✅ Google Gemini API: Connected
✅ Environment variables: Loaded
✅ Database: Ready
✅ Ready for interviews!
```

### Test 3: Manual API Test

**For Gemini:**
```bash
node -e "
const genAI = require('@google/generative-ai').GoogleGenerativeAI;
const key = process.env.GOOGLE_API_KEY;
console.log('Testing Gemini...');
console.log('Key loaded:', !!key);
"
```

**For OpenAI:**
```bash
node -e "
const { OpenAI } = require('openai');
const key = process.env.OPENAI_API_KEY;
console.log('Testing OpenAI...');
console.log('Key loaded:', !!key);
"
```

### Test 4: Start Dev Server

```bash
npm run dev
```

Visit `http://localhost:3000` and ask a test question.

---

## Troubleshooting

### "API Key not found" Error

**Solution:**
1. Check `.env.local` exists in the right folder
2. Verify no typos in variable names
3. Restart dev server: `Ctrl+C` then `npm run dev`
4. Check file has correct permissions

### "Rate limit exceeded"

**For Gemini:**
- Wait 1 minute or switch to OpenAI
- Gemini has 60 req/min limit

**For OpenAI:**
- Switch to Gemini temporarily
- Upgrade OpenAI billing tier

### "Invalid API Key"

**For Gemini:**
1. Go to [AI Studio](https://aistudio.google.com/app/apikey)
2. Delete old key, create new one
3. Copy the full key again (check for spaces)

**For OpenAI:**
1. Go to [API Keys](https://platform.openai.com/api/keys)
2. Delete old key, create new one
3. Verify account has active billing

### Slow Responses (> 2 seconds)

**Causes & Fixes:**
1. **Network issue** - Check internet speed
2. **Server overload** - Try again in 30 seconds
3. **Model busy** - Switch model or AI provider
4. **Too many tokens** - Use "quick" response type

```typescript
// Try quick response
{
  question: "Your question",
  type: "quick",  // Instead of "detailed"
}
```

### API Returns 401/403 Unauthorized

**Solution:**
1. Verify API key in `.env.local`
2. Check key hasn't expired
3. Verify key has correct permissions:
   - **Gemini**: Should have "AI Studio" permission
   - **OpenAI**: Should have "Chat Completions" permission

---

## Switching Between Models

### At Runtime (in Code)

```typescript
// In .env.local, comment out one:

// Use Gemini:
GOOGLE_API_KEY=AIzaSy...
AI_PROVIDER=gemini

// Use OpenAI:
// OPENAI_API_KEY=sk-...
// AI_PROVIDER=openai
```

### Fallback Strategy (Use Both)

```typescript
// Use Gemini by default, OpenAI as fallback
if (process.env.GOOGLE_API_KEY) {
  useGemini();
} else if (process.env.OPENAI_API_KEY) {
  useOpenAI();
} else {
  throw new Error("No AI provider configured");
}
```

---

## Security Best Practices

### 🔒 Never Commit API Keys

1. Add to `.gitignore`:
   ```
   .env.local
   .env.*.local
   *.key
   ```

2. Use `.env.example` for documentation:
   ```env
   # .env.example
   GOOGLE_API_KEY=your_key_here
   OPENAI_API_KEY=sk-your_key_here
   ```

3. Don't share keys in commits:
   ```bash
   # Check before committing
   git diff --cached | grep -i "key\|token\|secret"
   ```

### 🛡️ Rotate Keys Regularly

**Gemini:**
- Delete old keys monthly
- Keep only 2-3 active keys

**OpenAI:**
- Rotate monthly
- Use organization-level keys for teams
- Monitor usage in [API Dashboard](https://platform.openai.com/usage/overview)

### ⚠️ Monitor Costs (OpenAI)

```bash
# Check current usage
# Go to: https://platform.openai.com/account/billing/overview

# Or via API (requires organization key):
curl https://api.openai.com/v1/billing/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## Performance Optimization

### For Fastest Responses

1. **Use Gemini** (Free + Fast)
   ```env
   AI_PROVIDER=gemini
   GEMINI_MODEL=gemini-1.5-flash  # Faster than standard
   ```

2. **Set Temperature Low**
   ```typescript
   temperature: 0.2  // Less randomness = faster
   ```

3. **Limit Response Tokens**
   ```typescript
   maxTokens: 300  // Quick answers only
   ```

4. **Use Caching**
   ```typescript
   // Cache common interview questions
   const cache = new Map();
   if (cache.has(question)) return cache.get(question);
   ```

---

## Pricing Comparison

| Factor | Gemini | OpenAI |
|--------|--------|--------|
| Cost | FREE | $0.0004/question |
| Setup Time | 2 minutes | 5 minutes |
| Speed | ⚡⚡⚡ Fast | ⚡⚡⚡ Fast |
| Accuracy | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent |
| Rate Limit | 60/min | 3500/min |
| Support | Community | Paid Support |

**Recommendation:** Start with **Gemini (Free)**, switch to **OpenAI** if needed.

---

## Getting Help

### Check API Status
- [Gemini Status](https://status.cloud.google.com/)
- [OpenAI Status](https://status.openai.com/)

### Common Issues
- [Gemini Troubleshooting](https://ai.google.dev/troubleshooting)
- [OpenAI Help Center](https://help.openai.com/)

### Debug Logs
```bash
# Enable verbose logging
DEBUG=* npm run dev

# Check specific provider logs
npm run dev -- --inspect
```

---

## Next Steps

1. ✅ Choose your AI provider (Gemini or OpenAI)
2. ✅ Get API key (2 minutes)
3. ✅ Add to `.env.local` (1 minute)
4. ✅ Run `npm run verify-setup`
5. ✅ Start interviewing! `npm run dev`

**Ready?** Let's get your interview assistant running! 🚀
