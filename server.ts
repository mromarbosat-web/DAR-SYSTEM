import express from "express";
import path from "path";
import fs from "fs";
import dotenv from "dotenv";
import { createServer as createViteServer } from "vite";

dotenv.config();

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // API Route: Health Check
  app.get("/api/health", (req, res) => {
    res.json({
      status: "ok",
      timestamp: new Date().toISOString(),
      app: "Security & Management Bot Web Hub"
    });
  });

  // API Route: Get Bot Status & Env State
  app.get("/api/bot/status", (req, res) => {
    const hasToken = Boolean(process.env.DISCORD_BOT_TOKEN && process.env.DISCORD_BOT_TOKEN !== "your_discord_bot_token_here");
    const hasDb = Boolean(process.env.DATABASE_URL && !process.env.DATABASE_URL.includes("example.supabase.co"));

    res.json({
      configured: hasToken && hasDb,
      hasToken,
      hasDb,
      databaseUrl: process.env.DATABASE_URL || "postgresql+asyncpg://postgres:password@db.example.supabase.co:5432/postgres",
      environment: process.env.ENVIRONMENT || "production",
      pythonVersion: "3.11+",
      botVersion: "1.0.0",
      architecture: "Python discord.py + Supabase PostgreSQL + Railway Worker"
    });
  });

  // API Route: Get Python Codebase Structure & Files
  app.get("/api/bot/files", (req, res) => {
    const getFilesRecursively = (dir: string, baseDir: string = dir): any[] => {
      let results: any[] = [];
      if (!fs.existsSync(dir)) return results;

      const list = fs.readdirSync(dir);
      list.forEach((file) => {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);
        const relativePath = path.relative(process.cwd(), filePath);

        if (stat && stat.isDirectory()) {
          if (file !== "node_modules" && file !== ".git" && file !== "dist") {
            results.push({
              name: file,
              path: relativePath,
              type: "directory",
              children: getFilesRecursively(filePath, baseDir)
            });
          }
        } else {
          results.push({
            name: file,
            path: relativePath,
            type: "file",
            size: stat.size
          });
        }
      });
      return results;
    };

    const fileTree = [
      ...getFilesRecursively(path.join(process.cwd(), "bot")),
      { name: "requirements.txt", path: "requirements.txt", type: "file" },
      { name: "Dockerfile", path: "Dockerfile", type: "file" },
      { name: "Procfile", path: "Procfile", type: "file" },
      { name: "railway.json", path: "railway.json", type: "file" },
      { name: "schema.sql", path: "schema.sql", type: "file" },
      { name: ".env.example", path: ".env.example", type: "file" },
      { name: "README.md", path: "README.md", type: "file" }
    ];

    res.json({ files: fileTree });
  });

  // API Route: Read File Content
  app.get("/api/bot/file-content", (req, res) => {
    const filePathStr = req.query.path as string;
    if (!filePathStr) {
      return res.status(400).json({ error: "Missing path query parameter" });
    }

    const safePath = path.resolve(process.cwd(), filePathStr);
    if (!safePath.startsWith(process.cwd())) {
      return res.status(403).json({ error: "Access denied" });
    }

    try {
      if (fs.existsSync(safePath)) {
        const content = fs.readFileSync(safePath, "utf-8");
        return res.json({ path: filePathStr, content });
      } else {
        return res.status(404).json({ error: "File not found" });
      }
    } catch (e: any) {
      return res.status(500).json({ error: e.message });
    }
  });

  // API Route: Simulate Discord Security Events
  app.post("/api/bot/simulate", (req, res) => {
    const { type, payload } = req.body;

    if (type === "anti_raid") {
      const joinCount = payload?.joinCount || 8;
      const window = payload?.window || 10;
      const action = payload?.action || "lockdown";
      const isTriggered = joinCount >= 5;

      return res.json({
        event: "member_join_batch",
        guildId: "123456789012345678",
        joinCount,
        windowSeconds: window,
        triggered: isTriggered,
        actionTaken: isTriggered ? action.toUpperCase() : "NONE",
        logEmbed: isTriggered ? {
          title: "🛡️ تم اكتشاف هجوم دخول جماعي (Anti-Raid Triggered)",
          color: "#EB459E",
          fields: [
            { name: "عدد الانضمامات", value: `${joinCount} أعضاء خلال ${window}s`, inline: true },
            { name: "الإجراء الوقائي", value: action.toUpperCase(), inline: true },
            { name: "الحالة", value: "Locked down 12 channels for @everyone", inline: false }
          ]
        } : null
      });
    }

    if (type === "automod") {
      const text = payload?.content || "";
      let flagged = false;
      let reason = "";

      if (text.includes("discord.gg/") || text.includes("discord.com/invite")) {
        flagged = true;
        reason = "نشر رابط دعوة ديسكورد (Discord Invite Blocked)";
      } else if (text.toLowerCase().includes("badword") || text.includes("شتيمة")) {
        flagged = true;
        reason = "استخدام كلمة محظورة (Blacklisted Word)";
      } else if ((text.match(/@/g) || []).length > 3) {
        flagged = true;
        reason = "منشن جماعي مكثف (Mass Mention Detected)";
      }

      return res.json({
        event: "message_scan",
        content: text,
        flagged,
        reason: flagged ? reason : "Message passed AutoMod filters cleanly.",
        action: flagged ? "DELETE_MESSAGE_AND_WARN" : "ALLOW"
      });
    }

    if (type === "warn_ladder") {
      const currentWarns = (payload?.currentWarns || 0) + 1;
      let action = "WARN_RECORDED";
      let escalationNote = "";

      if (currentWarns === 3) {
        action = "TIMEOUT_1H";
        escalationNote = "تم تطبيق عزل مؤقت لمدة ساعة لتجاوز 3 تحذيرات!";
      } else if (currentWarns === 5) {
        action = "KICK";
        escalationNote = "تم طرد العضو من السيرفر لتجاوز 5 تحذيرات!";
      } else if (currentWarns >= 7) {
        action = "BAN";
        escalationNote = "تم حظر العضو نهائيًا لتجاوز 7 تحذيرات!";
      }

      return res.json({
        event: "warn_user",
        warningId: "warn_" + Math.random().toString(36).substring(2, 9),
        totalWarns: currentWarns,
        escalation: action,
        note: escalationNote || "تم تسجيل التحذير بنجاح."
      });
    }

    if (type === "voice_action") {
      const { action, member, channel, targetChannel, userLimit } = payload || {};
      return res.json({
        event: "voice_management",
        action: action || "MOVE",
        executor: "Admin_101",
        targetMember: member || "User_404",
        sourceChannel: channel || "General Voice #1",
        targetChannel: targetChannel || "Gaming Lounge #2",
        status: "SUCCESS",
        details: `Voice action '${action}' completed successfully with Role Hierarchy validation.`
      });
    }

    return res.status(400).json({ error: "Unknown simulation type" });
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
