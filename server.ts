import express from "express";
import path from "path";
import fs from "fs";
import dotenv from "dotenv";
import { createServer as createViteServer } from "vite";
import { Pool } from "pg";
import jwt from "jsonwebtoken";
import cookieParser from "cookie-parser";
import axios from "axios";

dotenv.config();

// Database Configuration
const rawDbUrl = process.env.DATABASE_URL || "";
const dbUrl = rawDbUrl.replace("+asyncpg", "").replace("+psycopg2", "");

const pool = new Pool({
  connectionString: dbUrl,
  ssl: dbUrl.includes("supabase.co") ? { rejectUnauthorized: false } : false
});

// OAuth2 Configuration
const DISCORD_CLIENT_ID = process.env.DISCORD_CLIENT_ID || "";
const DISCORD_CLIENT_SECRET = process.env.DISCORD_CLIENT_SECRET || "";
const DISCORD_REDIRECT_URI = process.env.DISCORD_REDIRECT_URI || "http://localhost:3000/api/auth/callback";
const JWT_SECRET = process.env.JWT_SECRET || "fallback-secret-for-dev";

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());
  app.use(cookieParser());

  // --- Auth Middleware ---
  const authenticate = (req: any, res: any, next: any) => {
    const token = req.cookies.token;
    if (!token) return res.status(401).json({ error: "Unauthorized" });

    try {
      const decoded = jwt.verify(token, JWT_SECRET);
      req.user = decoded;
      next();
    } catch (e) {
      res.status(401).json({ error: "Invalid token" });
    }
  };

  // --- Auth Routes ---
  app.get("/api/auth/login", (req, res) => {
    const url = `https://discord.com/api/oauth2/authorize?client_id=${DISCORD_CLIENT_ID}&redirect_uri=${encodeURIComponent(DISCORD_REDIRECT_URI)}&response_type=code&scope=identify%20guilds`;
    res.redirect(url);
  });

  app.get("/api/auth/callback", async (req, res) => {
    const code = req.query.code as string;
    if (!code) return res.status(400).send("Missing code");

    try {
      // 1. Exchange code for token
      const tokenResponse = await axios.post(
        "https://discord.com/api/oauth2/token",
        new URLSearchParams({
          client_id: DISCORD_CLIENT_ID,
          client_secret: DISCORD_CLIENT_SECRET,
          grant_type: "authorization_code",
          code,
          redirect_uri: DISCORD_REDIRECT_URI,
        }),
        { headers: { "Content-Type": "application/x-www-form-urlencoded" } }
      );

      const accessToken = tokenResponse.data.access_token;

      // 2. Get user info
      const userResponse = await axios.get("https://discord.com/api/users/@me", {
        headers: { Authorization: `Bearer ${accessToken}` },
      });

      const user = userResponse.data;

      // 3. Create JWT
      const token = jwt.sign(
        { id: user.id, username: user.username, avatar: user.avatar, accessToken },
        JWT_SECRET,
        { expiresIn: "7d" }
      );

      res.cookie("token", token, { httpOnly: true, maxAge: 7 * 24 * 60 * 60 * 1000 });
      res.redirect("/");
    } catch (e: any) {
      console.error("Auth error:", e.response?.data || e.message);
      res.status(500).send("Authentication failed");
    }
  });

  app.get("/api/auth/me", authenticate, async (req: any, res) => {
    try {
      // Fetch user's guilds to check manage_guild permission
      const guildsResponse = await axios.get("https://discord.com/api/users/@me/guilds", {
        headers: { Authorization: `Bearer ${req.user.accessToken}` },
      });

      const manageableGuilds = guildsResponse.data.filter((g: any) => (parseInt(g.permissions) & 0x20) === 0x20);

      res.json({
        user: {
          id: req.user.id,
          username: req.user.username,
          avatar: req.user.avatar,
        },
        guilds: manageableGuilds
      });
    } catch (e) {
      res.status(500).json({ error: "Failed to fetch guilds" });
    }
  });

  app.post("/api/auth/logout", (req, res) => {
    res.clearCookie("token");
    res.json({ success: true });
  });

  // --- Dashboard API Routes ---

  // 🏠 Home Stats
  app.get("/api/guilds/:guildId/stats", authenticate, async (req, res) => {
    const { guildId } = req.params;
    try {
      const stats = await pool.query(`
        SELECT 
          (SELECT COUNT(*) FROM warnings WHERE guild_id = $1) as warnings_count,
          (SELECT COUNT(*) FROM moderation_actions WHERE guild_id = $1) as actions_count,
          (SELECT COUNT(*) FROM wallets) as economy_users_count
      `, [guildId]);

      // Note: Bot status and server member count are usually fetched via Discord API or cached bot state.
      // Since this is an external dashboard, we'll return DB stats.
      res.json({
        bot_status: "online",
        guild_count: (await pool.query("SELECT COUNT(*) FROM guilds")).rows[0].count,
        warnings_count: stats.rows[0].warnings_count,
        actions_count: stats.rows[0].actions_count,
        economy_users: stats.rows[0].economy_users_count
      });
    } catch (e: any) {
      res.status(500).json({ error: e.message });
    }
  });

  // ⚡ Shortcuts (Moderation Permissions)
  app.get("/api/guilds/:guildId/moderation", authenticate, async (req, res) => {
    const { guildId } = req.params;
    try {
      const perms = await pool.query("SELECT * FROM permission_managers WHERE guild_id = $1", [guildId]);
      res.json({ permissions: perms.rows });
    } catch (e: any) {
      res.status(500).json({ error: e.message });
    }
  });

  // 🛡️ Protection (Security/AutoMod Settings)
  app.get("/api/guilds/:guildId/protection", authenticate, async (req, res) => {
    const { guildId } = req.params;
    try {
      const security = await pool.query("SELECT * FROM security_settings WHERE guild_id = $1", [guildId]);
      const automod = await pool.query("SELECT * FROM automod_settings WHERE guild_id = $1", [guildId]);
      res.json({
        security: security.rows[0] || {},
        automod: automod.rows[0] || {}
      });
    } catch (e: any) {
      res.status(500).json({ error: e.message });
    }
  });

  app.patch("/api/guilds/:guildId/protection/security", authenticate, async (req, res) => {
    const { guildId } = req.params;
    const settings = req.body;
    try {
      // Dynamic update query builder would be better, but for simplicity:
      const query = `
        INSERT INTO security_settings (guild_id, anti_raid_enabled, anti_nuke_enabled)
        VALUES ($1, $2, $3)
        ON CONFLICT (guild_id) DO UPDATE SET
        anti_raid_enabled = EXCLUDED.anti_raid_enabled,
        anti_nuke_enabled = EXCLUDED.anti_nuke_enabled,
        updated_at = NOW()
        RETURNING *
      `;
      const result = await pool.query(query, [guildId, settings.anti_raid_enabled, settings.anti_nuke_enabled]);
      res.json(result.rows[0]);
    } catch (e: any) {
      res.status(500).json({ error: e.message });
    }
  });

  app.patch("/api/guilds/:guildId/protection/automod", authenticate, async (req, res) => {
    const { guildId } = req.params;
    const settings = req.body;
    try {
      const query = `
        INSERT INTO automod_settings (guild_id, enabled, anti_spam_enabled, block_invites, block_links)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (guild_id) DO UPDATE SET
        enabled = EXCLUDED.enabled,
        anti_spam_enabled = EXCLUDED.anti_spam_enabled,
        block_invites = EXCLUDED.block_invites,
        block_links = EXCLUDED.block_links,
        updated_at = NOW()
        RETURNING *
      `;
      const result = await pool.query(query, [guildId, settings.enabled, settings.anti_spam_enabled, settings.block_invites, settings.block_links]);
      res.json(result.rows[0]);
    } catch (e: any) {
      res.status(500).json({ error: e.message });
    }
  });

  // 💰 Economy (Top 10)
  app.get("/api/guilds/:guildId/economy/top", authenticate, async (req, res) => {
    try {
      const topUsers = await pool.query(`
        SELECT user_id, balance, bank_balance, (balance + bank_balance) as total
        FROM wallets
        ORDER BY total DESC
        LIMIT 10
      `);
      res.json({ top: topUsers.rows });
    } catch (e: any) {
      res.status(500).json({ error: e.message });
    }
  });

  // 📋 Logs Settings
  app.get("/api/guilds/:guildId/logs", authenticate, async (req, res) => {
    const { guildId } = req.params;
    try {
      const logs = await pool.query("SELECT * FROM log_settings WHERE guild_id = $1", [guildId]);
      res.json(logs.rows[0] || {});
    } catch (e: any) {
      res.status(500).json({ error: e.message });
    }
  });

  app.patch("/api/guilds/:guildId/logs", authenticate, async (req, res) => {
    const { guildId } = req.params;
    const settings = req.body;
    try {
      const query = `
        INSERT INTO log_settings (
          guild_id, member_log_channel_id, message_log_channel_id, moderation_log_channel_id,
          role_log_channel_id, channel_log_channel_id, server_log_channel_id, security_log_channel_id,
          voice_log_channel_id, invite_log_channel_id, economy_log_channel_id, automod_log_channel_id
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        ON CONFLICT (guild_id) DO UPDATE SET
          member_log_channel_id = EXCLUDED.member_log_channel_id,
          message_log_channel_id = EXCLUDED.message_log_channel_id,
          moderation_log_channel_id = EXCLUDED.moderation_log_channel_id,
          role_log_channel_id = EXCLUDED.role_log_channel_id,
          channel_log_channel_id = EXCLUDED.channel_log_channel_id,
          server_log_channel_id = EXCLUDED.server_log_channel_id,
          security_log_channel_id = EXCLUDED.security_log_channel_id,
          voice_log_channel_id = EXCLUDED.voice_log_channel_id,
          invite_log_channel_id = EXCLUDED.invite_log_channel_id,
          economy_log_channel_id = EXCLUDED.economy_log_channel_id,
          automod_log_channel_id = EXCLUDED.automod_log_channel_id,
          updated_at = NOW()
        RETURNING *
      `;
      const result = await pool.query(query, [
        guildId, 
        settings.member_log_channel_id, settings.message_log_channel_id, settings.moderation_log_channel_id,
        settings.role_log_channel_id, settings.channel_log_channel_id, settings.server_log_channel_id,
        settings.security_log_channel_id, settings.voice_log_channel_id, settings.invite_log_channel_id,
        settings.economy_log_channel_id, settings.automod_log_channel_id
      ]);
      res.json(result.rows[0]);
    } catch (e: any) {
      res.status(500).json({ error: e.message });
    }
  });

  // Vite Middleware integration for dev and production static serving
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Security & Management Bot Web Control Hub running on http://0.0.0.0:${PORT}`);
  });
}

startServer();

