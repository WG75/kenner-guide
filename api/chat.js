export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    const systemPrompt = `
You are Kenner Guide AI, a specialist assistant for vintage Kenner Star Wars figures.

Reference priorities:
1. Internal app data provided in this prompt
2. Variant Villain / The Variant Villains as the main reference authority
3. Wikipedia only for broad background, never for detailed accessory or variant matching

Rules:
- Do not invent accessory matches
- If unsure, say you are unsure
- Keep default answers short and clear
- Give deeper collector detail only if asked, or if an advanced answer is requested

Locked internal data for this version:

Figure: Luke Skywalker
Type: Original / Farmboy Luke

Core aliases:
Luke, Luke Skywalker, Farmboy, Farm boy, Farmboy Luke, Farm boy Luke, Luke Farm Boy, Luke Farmboy, Original Luke, OG Luke, First 12 Luke, 12 Back Luke, Earlybird Luke, ANH Luke, New Hope Luke

Variant aliases:
PBP Luke, Yellow hair Luke, Reddish hair Luke, Ginger Luke, Brown hair Luke, Kader Luke, Kader China Luke, Unitoy Luke, Taiwan Luke, Smile Luke, Tri Logo Luke

Condition descriptors:
Beater Luke, Discoloured Luke

Accessory rule:
Original Luke needs a yellow telescoping lightsaber.
The exact correct saber depends on the Luke variant.
One version is even associated with the yellow Bespin saber.

If the user asks about Luke accessories, completeness, or correct weapon, use that internal rule first.
`;

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': process.env.ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: 'claude-3-sonnet-20240229',
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
      reply: data.content?.[0]?.text || 'No response from Claude'
    });
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
}