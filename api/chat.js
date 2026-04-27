// ONLY showing the changed section to keep this readable for you
// (rest of your file stays EXACTLY the same)

function offTopicResponse() {
  const variants = [
    `Sorry, I’m not familiar with that subject.

I’m a Collector Companion droid focused on vintage Star Wars toys from 1977 to 1985, mostly the figures and accessories.

If you meant something vintage Star Wars related, please clarify and I’ll help.

Do you have any vintage Star Wars questions I can help with?`,

    `Sorry, that’s outside my collector database.

I focus on vintage Kenner Star Wars toys from 1977 to 1985 — figures, variants, COOs and accessories.

If you meant a figure or accessory, tell me which one and I’ll guide you.

Do you have any vintage Star Wars related questions?`,

    `I’m sorry, I can’t help with that.

I’m a Collector Companion droid for vintage Star Wars figures and accessories from 1977 to 1985.

If you meant something from that era, just let me know and I’ll help.`
  ];

  return {
    reply: variants[Math.floor(Math.random() * variants.length)],
    images: [],
    flowState: null
  };
}