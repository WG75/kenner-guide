export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).json({
      reply: "Method not allowed"
    });
  }

  try {
    const { message, image } = req.body;

    // -----------------------------------
    // IMAGE ANALYSIS MODE
    // -----------------------------------

    if (image) {
      const response = await fetch("https://api.openai.com/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`
        },
        body: JSON.stringify({
          model: "gpt-4o-mini",
          messages: [
            {
              role: "system",
              content: `
You are VF-CB, a Vintage Kenner Star Wars figure identification assistant.

Your job:
- identify the broad figure family only
- NOT exact variants yet
- detect if item appears modern, fake, bootleg or unrelated

Allowed broad categories:

Luke Skywalker (Original / Tatooine / Farm boy)
Luke Skywalker (X-Wing Pilot)
Luke Skywalker (Bespin)
Luke Skywalker (Hoth)
Luke Skywalker (Jedi Knight)
Luke Skywalker (Endor)
Luke Skywalker (Stormtrooper)

Princess Leia
Han Solo
Darth Vader
Stormtrooper
Jawa
Tusken Raider
Obi-Wan Kenobi
Chewbacca
C-3PO
R2-D2

If uncertain, say uncertain.

Keep responses concise.
`
            },
            {
              role: "user",
              content: [
                {
                  type: "text",
                  text: "Identify this vintage Star Wars figure."
                },
                {
                  type: "image_url",
                  image_url: {
                    url: image
                  }
                }
              ]
            }
          ],
          max_tokens: 200
        })
      });

      const data = await response.json();

      console.log("OPENAI RESPONSE:", JSON.stringify(data, null, 2));

      const reply =
        data?.choices?.[0]?.message?.content ||
        "I could not identify the figure from that image.";

      return res.status(200).json({
        reply
      });
    }

    // -----------------------------------
    // NORMAL CHAT MODE
    // -----------------------------------

    return res.status(200).json({
      reply:
        "Photo upload is connected. Text-only collector chat still needs reconnecting."
    });

  } catch (error) {
    console.error(error);

    return res.status(500).json({
      reply: "Something went wrong analysing the image."
    });
  }
}