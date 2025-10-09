import fs from "fs";
import path from "path";

export default function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ error: "Method not allowed" });

  const { email, password } = req.body;
  if (!email || !password) return res.status(400).json({ error: "Email & password required" });

  // Read users.json
  const filePath = path.join(process.cwd(), "users.json");
  const users = JSON.parse(fs.readFileSync(filePath, "utf-8"));

  const user = users.find(u => u.email === email && u.password === password);
  if (!user) return res.status(401).json({ error: "Invalid credentials" });

  // Return user profile directly
  res.status(200).json({
    success: true,
    profile: { email: user.email, balance: user.balance }
  });
}
