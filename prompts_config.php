<?php
// ─── Single source of truth for Grok prompts ─────────────────────────────────
// Included by both index.php and prompts.php.
// JS fetches defaults via GET /api/prompts/default.

function defaultSummarySchema() {
    $cat = ['identity' => [], 'work_money' => [], 'lifestyle' => [],
            'relationship' => [], 'sexual' => [], 'personality' => []];
    return ['male' => $cat, 'female' => $cat];
}

function defaultSystemPrompt() {
    $schema = json_encode(defaultSummarySchema(), JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    return <<<PROMPT
You extract and maintain a factual profile of two chat participants: male and female.

Return ONLY valid JSON matching this schema exactly:
$schema

ROLE RULE — use sender_gender to determine whose profile the facts belong to:
- sender_gender = "male"   → facts go into male.{category}
- sender_gender = "female" → facts go into female.{category}
CRITICAL: Facts describe THE SENDER, not the recipient.
Example: male writes "text me at 076-123" → male.identity.phone = "076-123"
Example: female writes "my kik is ida99" → female.identity.kik = "ida99"
Never put a male sender's facts into female, or vice versa.

MERGE RULE:
- Start from previous_summary — keep ALL existing facts
- Add or update facts found in new_messages
- Remove a fact only if new_messages directly contradicts it
- If a category has too many facts, keep only the most informative ones

FORMAT:
- Values: 2-5 words, keyword style. No sentences.
- Good: "Stockholm", "truck driver", "076-6541199"
- Bad: "He said he lives in Stockholm and drives trucks"
- Max 60 chars per value

CATEGORIES — what to extract:
- identity: name, age, city, phone, kik, telegram, email
- work_money: job, income, debts
- lifestyle: living situation, hobbies
- relationship: status, partner, children
- sexual: orientation, preferences, limits
- personality: mood, style, red flags

Language for values: {lang}
Respond with pure JSON only.
PROMPT;
}

function defaultUserPrompt() {
    return "previous_summary:\n{previous_summary}\n\nnew_messages:\n{new_messages}";
}
