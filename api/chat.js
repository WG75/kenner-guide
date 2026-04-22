export default async function handler(req, res) {
  console.log("🔥 NEW VERSION HIT");

  return res.status(200).json({
    reply: "TEST SUCCESS - NEW FUNCTION IS RUNNING"
  });
}