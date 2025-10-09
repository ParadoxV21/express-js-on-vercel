import fs from "fs";
import path from "path";
import type { VercelRequest, VercelResponse } from "@vercel/node";

interface User {
  email: string;
  password: string;
  balance: number;
}

export default function handler(req: VercelRequest, res: VercelResponse) {
  const filePath = path.join(process.cwd(), "users.json");
  const users: User[] = JSON.parse(fs.readFileSync(filePath, "utf-8"));

  // Route handling
  if (req.url?.startsWith("/login") && req.method === "POST") {
    const { email, password } = req.body as { email?: string; password?: string };
    if (!email || !password) return res.status(400).json({ error: "Email & password required" });

    const user = users.find(u => u.email === email && u.password === password);
    if (!user) return res.status(401).json({ error: "Invalid credentials" });

    return res.status(200).json({ success: true, profile: { email: user.email, balance: user.balance } });
  }

  if (req.url?.startsWith("/profile") && req.method === "GET") {
    const email = req.headers["x-email"] as string;
    const password = req.headers["x-password"] as string;
    if (!email || !password) return res.status(400).json({ error: "Email & password required" });

    const user = users.find(u => u.email === email && u.password === password);
    if (!user) return res.status(401).json({ error: "Invalid credentials" });

    return res.status(200).json({ email: user.email, balance: user.balance });
  }

  // Default response for unknown route
  res.status(404).json({ error: "Route not found" });
}
