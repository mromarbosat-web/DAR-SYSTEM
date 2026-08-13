import express from "express";
import dotenv from "dotenv";

dotenv.config();

const app = express();
const PORT = 3000;

app.get("*", (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Security Bot Status</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
            body { font-family: 'Cairo', sans-serif; background-color: #000; color: #fff; }
        </style>
    </head>
    <body class="flex items-center justify-center min-h-screen">
        <div class="text-center p-8 border border-zinc-800 rounded-3xl bg-zinc-900 shadow-2xl">
            <div class="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <div class="w-4 h-4 bg-green-500 rounded-full animate-pulse"></div>
            </div>
            <h1 class="text-3xl font-bold mb-2">البوت يعمل بنجاح</h1>
            <p class="text-zinc-400">Security & Management Bot is Active</p>
            <div class="mt-8 pt-6 border-t border-zinc-800 text-xs text-zinc-600 uppercase tracking-widest">
                إدارة كاملة عبر Discord Slash Commands
            </div>
        </div>
    </body>
    </html>
  `);
});

app.listen(PORT, () => {
  console.log(`Status server running on http://localhost:${PORT}`);
});
