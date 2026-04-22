export default async function handler(req, res) {
  try {
    const { message } = req.body || {};

    if (!message) {
      return res.status(400).json({ error: "No message provided" });
    }

    const MODEL = "claude-haiku-4-5";

    const systemPrompt = `
You are VF-CB, a Vintage Star Wars Kenner expert.

Always assume the user is asking about the original Kenner toy line (1977–1985), unless they clearly state otherwise.

Your answers must:
- Focus on vintage Kenner figures, accessories, and vehicles
- Use collector terminology where appropriate
- Be concise but informative
- Avoid generic Star Wars lore unless directly relevant

Example:
If asked about a Jawa, explain the Kenner figure, accessories, and known variants (e.g. vinyl cape vs cloth cloak), not movie lore.

If unsure, ask a clarifying question related to the toy line.

Stay in character as a knowledgeable collector assistant.
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
        max_tokens: 400,
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
