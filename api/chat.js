export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  try {
    const { message, history = [] } = req.body || {};

    if (!message || typeof message !== "string") {
      return res.status(400).json({ error: "Missing message" });
    }

    const apiKey = process.env.ANTHROPIC_API_KEY;

    if (!apiKey) {
      return res.status(500).json({ error: "Missing ANTHROPIC_API_KEY" });
    }

    const systemPrompt = `
You are VF-CB, the Vintage Figures Chat Bot.

You are an expert on vintage Kenner Star Wars figures, accessories, variants, COO markings, cardbacks and collecting terminology.

Style rules:
- Be confident, direct and helpful
- Speak like a knowledgeable collector
- Do not waffle
- Do not say you are happy to help
- Do not ask unnecessary clarification questions if the answer is obvious from collector context
- If the user says Chewy, understand they almost certainly mean Chewbacca
- If the user asks a follow up question, use the prior conversation context
- Give practical collector facing answers
- If something is uncertain, say so plainly
- Prefer concise answers unless more detail is useful

Important:
- Stay focused on vintage Kenner Star Wars figures and related accessories or variants
- If the user asks something outside that scope, briefly say so
`;

    const messages = [];

    if (Array.isArray(history) && history.length) {
      for (const item of history.slice(-8)) {
        if (!item || !item.role || !item.content) continue;
        if (item.role !== "user" && item.role !== "assistant") continue;

        messages.push({
          role: item.role,
          content: [
            {
              type: "text",
              text: String(item.content),
            },
          ],
        });
      }
    }

    messages.push({
      role: "user",
      content: [
        {
          type: "text",
          text: message,
        },
      ],
    });

    const anthropicRes = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": apiKey,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: "claude-3-5-haiku-latest",
        max_tokens: 600,
        temperature: 0.4,
        system: systemPrompt.trim(),
        messages,
      }),
    });

    const data = await anthropicRes.json();

    if (!anthropicRes.ok) {
      console.error("Anthropic API error:", data);
      return res.status(500).json({
        error: "Anthropic request failed",
        details: data,
      });
    }

    const reply =
      data?.content?.find((item) => item.type === "text")?.text ||
      "No response returned.";

    return res.status(200).json({ reply });
  } catch (error) {
    console.error("Server error:", error);
    return res.status(500).json({
      error: "Server error",
      details: error.message,
    });
  }
}