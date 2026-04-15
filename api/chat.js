import fs from 'fs';
import path from 'path';

function loadFigureData() {
  const basePath = path.join(process.cwd(), 'data/figures');
  const indexPath = path.join(basePath, 'index.json');

  if (!fs.existsSync(indexPath)) return [];

  const index = JSON.parse(fs.readFileSync(indexPath, 'utf-8'));

  return index.map(entry => {
    const filePath = path.join(process.cwd(), entry.file);
    if (!fs.existsSync(filePath)) return null;

    const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    return data;
  }).filter(Boolean);
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    // 🔍 Load figures + detect match
    const figures = loadFigureData();
    const lowerMsg = message.toLowerCase();

    let matchedFigure = null;

    for (const fig of figures) {
      if (fig.aliases.some(a => lowerMsg.includes(a))) {
        matchedFigure = fig;
        break;
      }
    }

    // 🧠 Build dynamic reference
    let dynamicReference = '';

    if (matchedFigure) {
      dynamicReference = `
Figure: ${matchedFigure.name}

Default:
${matchedFigure.defaultAnswer}

Advanced:
${Object.entries(matchedFigure.advanced)
  .map(([k, v]) => `- ${k}: ${v}`)
  .join('\n')}
`;
    }

    // 🤖 System prompt
    const systemPrompt = `
You are VF-CB, the Vintage Figures Chat Bot.

Rules:
- Use the reference data if available
- Keep answers short by default
- Expand only if needed
- Do not guess unknown info
- Speak like a knowledgeable collector

REFERENCE:
${dynamicReference}
`;

    // 🔗 Call Claude API
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 700,
        system: systemPrompt,
        messages: [
          {
            role: 'user',
            content: message
          }
        ]
      })
    });

    const data = await response.json();

    if (!response.ok) {
      return res.status(response.status).json(data);
    }

    return res.status(200).json({
      reply: data.content?.[0]?.text || 'No response'
    });

  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
}