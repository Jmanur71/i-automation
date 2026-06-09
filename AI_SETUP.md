# Getting Better AI Responses

## Problem
The default free providers (Wikipedia, DuckDuckGo) sometimes return incorrect or irrelevant answers.

## Solution Options

### Option 1: Use OpenAI (Best Quality)
1. Get free API key from https://platform.openai.com
2. Add to `~/.parakeet_settings.json`:
```json
{
  "ai_provider": "openai",
  "openai_api_key": "sk-proj-your-key-here"
}
```
3. Restart the app

### Option 2: Use Anthropic Claude
1. Get API key from https://console.anthropic.com
2. Add to `~/.parakeet_settings.json`:
```json
{
  "ai_provider": "anthropic",
  "anthropic_api_key": "sk-ant-your-key-here"
}
```
3. Restart the app

### Option 3: Use Groq (Free & Fast)
1. Get free API key from https://console.groq.com
2. Modify `groq_provider.py` line 9:
```python
self.api_key = "gsk_your-actual-key-here"
```
3. Update `settings_manager.py` to add "groq" as provider option
4. Restart the app

## Current Setup

**Default**: Uses Wikipedia + DuckDuckGo (free, no API key needed)
- ✅ No setup required
- ❌ Sometimes returns wrong answers
- ❌ Limited to factual queries

**OpenAI**: Best quality answers
- ✅ Most accurate responses
- ✅ Handles complex questions
- ❌ Requires API key ($)

**Anthropic**: High quality alternative
- ✅ Very accurate
- ✅ Good for technical questions
- ❌ Requires API key ($)

## Recommendation

For best results like Parakeet AI:
1. Get an OpenAI API key (they offer free credits)
2. Configure it in settings
3. Enjoy accurate AI responses

## Quick Test

```bash
# Edit settings file
notepad %USERPROFILE%\.parakeet_settings.json

# Add your API key
{
  "ai_provider": "openai",
  "openai_api_key": "sk-..."
}

# Restart
python main.py
```
