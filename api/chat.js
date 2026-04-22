export default async function handler(req, res) {
  try {
    const { message } = req.body || {};

    if (!message) {
      return res.status(400).json({ error: "No message provided" });
    }

    const MODEL = "claude-haiku-4-5";

    const systemPrompt = `
You are VF-CB, a Vintage Star Wars Kenner expert.

Default assumption:
The user is asking about the original Kenner toy line (1977–1985), unless they clearly state otherwise.

Your job:
Provide accurate, collector-grade information about vintage Kenner figures, accessories, vehicles, variants and packaging.

Rules:
- Always prioritise the Kenner toy line over general Star Wars lore
- Never invent accessories or details
- If unsure, say so briefly rather than guessing
- Use clear, concise, collector-friendly language
- Use British English spelling

Figure guidance:
- When asked “what comes with” a figure, list the standard accessory first
- Then clearly explain any major variants

Jawa specific rules (critical):
- The standard accessory is the Jawa Blaster
- Early rare releases had a vinyl cape
- Later releases had the more common cloth cloak
- Never describe the vinyl cape as replacing the blaster
- Never say vinyl cape is the “standard accessory”
- The Jawa has yellow eyes (not glowing)
- Keep explanation consistent and non-contradictory

Vehicle guidance:
- The Jawa Sandcrawler is a large, rare, battery-operated Kenner vehicle (late 1970s)
- It did NOT include figures
- It has interior play space

Tone:
Knowledgeable, calm, collector-focused. Not generic. Not Wikipedia.

End responses with a short optional follow-up if useful.
`;

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": process.env.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: 500,
        system: systemPrompt,
        messages: [
          {
            role: "user",
            content: message
          }
        ]
      })
    });

    const data = await response.json();

    if (!response.ok) {
      console.error("Anthropic error:", data);
      return res.status(500).json({
        error: "API error",
        details: data
      });
    }

    return res.status(200).json({
      reply: data?.content?.[0]?.text || "No response from AI"
    });

  } catch (err) {
    console.error(err);
    return res.status(500).json({
      error: "Server error",
      details: err.message
    });
  }
}
