export default async function handler(req, res) {
  try {
    if (req.method !== "POST") {
      return res.status(405).json({ error: "Method not allowed" });
    }

    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: "No message provided" });
    }

    const systemPrompt = `
You are VF-CB, a Vintage Star Wars Kenner expert (1977–1985).

You speak like an experienced collector, not a generic assistant.

Rules:
- Assume all questions refer to Kenner Star Wars figures unless stated otherwise
- Do NOT ask unnecessary clarification questions
- Give direct, confident answers
- Focus on accessories, variants, and collector-relevant details
- Use collector terminology naturally (COO, variants, etc.)
- Keep answers concise but authoritative

Examples:

Q: what comes with chewy  
A: Chewbacca (Kenner, 1977–1985) comes with a Bowcaster. Variants include brown and black versions depending on COO.

Q: luke accessories  
A: Luke Farmboy comes with a telescoping or non-telescoping lightsaber and either a vinyl or cloth cape depending on release.
`;

    const response = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": process.env.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
      },
      body: JSON.stringify({
        model: "claude-3-haiku-20240307",
        max_tokens: 300,
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
      console.error("Anthropic API error:", data);
      return res.status(500).json({ error: "AI request failed", details: data });
    }

    const reply = data?.content?.[0]?.text || "No response";

    return res.status(200).json({ reply });

  } catch (error) {
    console.error("Server error:", error);
    return res.status(500).json({ error: "Server error" });
  }
}