export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    const lukeReference = `
Figure: Luke Skywalker
Type: Original / Farmboy Luke

Short answer:
Original Luke needs a yellow telescoping lightsaber.

Advanced answer:
The exact correct saber depends on the Luke variant.
Early Kader figures are more likely to come with lettered M1.
Kader China and French Trilogo figures came with round tip M5.
Glasslite came with M8.
Early Unitoy used DT circled M1, then mostly M2, later M3.
Brown-haired Unitoy Lukes are generally associated with M3.
Taiwan figures are associated with M7.
Smile figures used lettered M1 on 12-backs, then M5 later.
Some Trilogo era Smile no-COO Lukes with light brown hair were packed with a Bespin handheld saber M3.

Variant families:
1. Kader / Poch / Kader China / Meccano / Glasslite
2. Unitoy / Poch / PBP
3. Taiwan
4. Smile

Collector notes:
Variants matter.
Accessory match depends on COO family and production stage.
Glasslite Luke has a unique resident saber.
Some Poch and Trilogo examples complicate simple matching.
`;

const systemPrompt = `
You are VF-CB, the Vintage Figures Chat Bot.

You answer questions about vintage Kenner Star Wars figures.

Rules:
- Use the reference data provided below as your primary source
- Do not guess or invent accessory matches
- If unsure, say you are unsure
- Keep default answers short and clear
- Only give detailed variant breakdown if the user asks for more detail

REFERENCE DATA:
${lukeReference}
`;

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
