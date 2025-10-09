import fs from "fs";
import path from "path";
import type { VercelRequest, VercelResponse } from "@vercel/node";

interface User {
  email: string;
  password: string;
  balance: number;
}

export default function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== "GET") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  const email = req.headers["x-email"] as string;
  const password = req.headers["x-password"] as string;

  if (!email || !password) {
    return res.status(400).json({ error: "Email & password required" });
  }

  const filePath = path.join(process.cwd(), "users.json");
  const users: User[] = JSON.parse(fs.readFileSync(filePath, "utf-8"));

  const user = users.find(u => u.email === email && u.password === password);

  if (!user) {
    return res.status(401).json({ error: "Invalid credentials" });
  }

  res.status(200).json({ email: user.email, balance: user.balance });
}
