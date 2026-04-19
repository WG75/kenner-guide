# VF-CB conversation memory pack

This pack gives your app basic conversation memory.

## Files included

- `api/chat.js`
- `public/vfcb-chat-memory.js`

## What this fixes

Your bot can now:
- remember the last few turns
- understand follow-up questions
- stop asking the user to repeat obvious context

## What you need to do

1. Replace your current `api/chat.js` with the one in this pack.
2. Add `public/vfcb-chat-memory.js` to your repo.
3. Load `vfcb-chat-memory.js` on the page where your chat box lives.
4. Use `sendVFChat(message)` instead of calling `/api/chat` directly.

## Important

This is a simple memory layer.
It is enough to make follow-up questions work properly.
